from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import List
from pathlib import Path
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.items import Item as ItemSchema, ItemCreate, ItemUpdate
from app.auth.deps import get_current_user
from app.db.models.user import User
from app.db.models.item import Item
from app.db.database import get_db
from app.core.config import settings
from app.ai.embeddings import embed_image_bytes

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


@router.get("/", response_model=List[ItemSchema])
async def list_items(db: AsyncSession = Depends(get_db)) -> List[Item]:
    res = await db.execute(select(Item).order_by(Item.id.desc()))
    return list(res.scalars().all())


@router.get("/{item_id}", response_model=ItemSchema)
async def get_item(item_id: int, db: AsyncSession = Depends(get_db)) -> Item:
    return await _get_item_or_404(db, item_id)


@router.post("/", response_model=ItemSchema, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Item:
    data = payload.model_dump()
    new_item = Item(**data, owner_id=user.id, status="OPEN")
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item


@router.post("/{item_id}/image", response_model=ItemSchema)
async def attach_image_to_item(
    item_id: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Item:
    """Attach an image to an existing item (MVP).

    - Saves image into MEDIA_DIR
    - Stores public `image_url` (served via StaticFiles)
    - Extracts and stores `embedding` for similarity search

    In production this upload should go to MinIO/S3 and `image_url` should be a
    presigned/public URL.
    """
    item = await _get_item_or_404(db, item_id)
    _ensure_owner(item, user.id)

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    # Save under uploads/items/<item_id>/<uuid>.<ext>
    ext = (Path(file.filename).suffix or ".jpg").lower()
    safe_ext = ext if len(ext) <= 10 else ".jpg"
    rel_dir = Path("items") / str(item_id)
    abs_dir = Path(settings.MEDIA_DIR) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{safe_ext}"
    abs_path = abs_dir / filename
    abs_path.write_bytes(data)

    item.image_url = f"/media/{rel_dir.as_posix()}/{filename}"
    item.embedding = embed_image_bytes(data)

    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=ItemSchema)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    user: User = Depends(get_current_user),
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
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_item_or_404(db, item_id)
    _ensure_owner(item, user.id)

    await db.delete(item)
    await db.commit()
    return
