from io import BytesIO
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_image_bytes
from app.auth.deps import require_not_banned
from app.core.config import settings
from app.db.database import get_db
from app.db.models.item import Item
from app.db.models.stored_file import StoredFile
from app.db.models.user import User
from app.schemas.items import (
    Item as ItemSchema,
    ItemCreate,
    ItemUpdate,
    ItemsPage,
    ItemsQuery,
)
from app.services.storage_s3 import delete_object, presign_get, upload_fileobj
from app.services.upload_validation import validate_image_upload

router = APIRouter(prefix="/items", tags=["items"])


async def _get_item_or_404(db: AsyncSession, item_id: int) -> Item:
    res = await db.execute(select(Item).where(Item.id == item_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


def _ensure_owner(item: Item, user_id: int) -> None:
    if item.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")


def _build_object_key(item_id: int, content_type: str) -> str:
    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    safe_ext = ext_map.get(content_type, ".jpg")
    return f"items/{item_id}/{uuid.uuid4().hex}{safe_ext}"


async def _get_item_image_file(db: AsyncSession, item_id: int) -> StoredFile | None:
    res = await db.execute(
        select(StoredFile).where(
            StoredFile.item_id == item_id,
            StoredFile.kind == "item_image",
        )
    )
    return res.scalar_one_or_none()


async def _attach_image_url(item: Item, db: AsyncSession) -> Item:
    image = await _get_item_image_file(db, item.id)
    item.image_url = presign_get(image.object_key) if image else None
    return item


async def _delete_all_item_files(db: AsyncSession, item_id: int) -> None:
    files_res = await db.execute(
        select(StoredFile).where(StoredFile.item_id == item_id)
    )
    files = list(files_res.scalars().all())

    for stored_file in files:
        try:
            delete_object(stored_file.object_key)
        except Exception:
            pass
        await db.delete(stored_file)


@router.get("/mine", response_model=list[ItemSchema])
async def list_my_items(
    user: User = Depends(require_not_banned),
    db: AsyncSession = Depends(get_db),
) -> list[Item]:
    res = await db.execute(
        select(Item)
        .where(Item.owner_id == user.id)
        .order_by(Item.id.desc())
    )
    items = list(res.scalars().all())

    for item in items:
        await _attach_image_url(item, db)

    return items


@router.get("/", response_model=ItemsPage)
async def list_items(
    qp: Annotated[ItemsQuery, Query()],
    db: AsyncSession = Depends(get_db),
) -> ItemsPage:
    stmt = select(Item)
    count_stmt = select(func.count()).select_from(Item)

    filters = []

    if qp.type:
        filters.append(Item.type == qp.type)

    if qp.status:
        filters.append(Item.status == qp.status)

    if qp.category:
        filters.append(Item.category == qp.category)

    if qp.q and qp.q.strip():
        like = f"%{qp.q.strip()}%"
        filters.append(
            or_(
                Item.title.ilike(like),
                Item.description.ilike(like),
                Item.roomLabel.ilike(like),
            )
        )

    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)

    if qp.sort == "id_desc":
        stmt = stmt.order_by(Item.id.desc())
    elif qp.sort == "id_asc":
        stmt = stmt.order_by(Item.id.asc())
    elif qp.sort == "title_asc":
        stmt = stmt.order_by(Item.title.asc(), Item.id.desc())
    elif qp.sort == "title_desc":
        stmt = stmt.order_by(Item.title.desc(), Item.id.desc())

    offset = (qp.page - 1) * qp.page_size
    stmt = stmt.offset(offset).limit(qp.page_size)

    total = (await db.execute(count_stmt)).scalar_one()
    items = list((await db.execute(stmt)).scalars().all())

    for item in items:
        await _attach_image_url(item, db)

    return ItemsPage(
        items=items,
        total=total,
        page=qp.page,
        page_size=qp.page_size,
    )


@router.get("/{item_id}", response_model=ItemSchema)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)) -> Item:
    item = await _get_item_or_404(db, item_id)
    return await _attach_image_url(item, db)


@router.post("/", response_model=ItemSchema, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    user: User = Depends(require_not_banned),
    db: AsyncSession = Depends(get_db),
) -> Item:
    data = payload.model_dump()
    new_item = Item(**data, owner_id=user.id, status="OPEN")
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return await _attach_image_url(new_item, db)


@router.post("/{item_id}/image", response_model=ItemSchema)
async def attach_image_to_item(
    item_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_not_banned),
    db: AsyncSession = Depends(get_db),
) -> Item:
    item = await _get_item_or_404(db, item_id)
    _ensure_owner(item, user.id)

    size_bytes = await validate_image_upload(file)
    content_type = (file.content_type or "").lower()
    data = await file.read()

    old_file = await _get_item_image_file(db, item.id)

    if old_file:
        try:
            delete_object(old_file.object_key)
        except Exception:
            pass
        await db.delete(old_file)
        await db.flush()

    object_key = _build_object_key(item.id, content_type)

    try:
        upload_fileobj(
            fileobj=BytesIO(data),
            object_key=object_key,
            content_type=content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

    stored = StoredFile(
        bucket=settings.S3_BUCKET,
        object_key=object_key,
        original_name=file.filename or "file",
        content_type=content_type,
        size_bytes=size_bytes,
        kind="item_image",
        owner_id=user.id,
        item_id=item.id,
    )
    db.add(stored)

    item.embedding = embed_image_bytes(data)

    await db.commit()
    await db.refresh(item)
    return await _attach_image_url(item, db)


@router.patch("/{item_id}", response_model=ItemSchema)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    user: User = Depends(require_not_banned),
    db: AsyncSession = Depends(get_db),
) -> Item:
    item = await _get_item_or_404(db, item_id)
    _ensure_owner(item, user.id)

    data = payload.model_dump(exclude_unset=True)
    data.pop("owner_id", None)

    for k, v in data.items():
        setattr(item, k, v)

    await db.commit()
    await db.refresh(item)
    return await _attach_image_url(item, db)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    user: User = Depends(require_not_banned),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_item_or_404(db, item_id)
    _ensure_owner(item, user.id)

    await _delete_all_item_files(db, item.id)

    await db.delete(item)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)