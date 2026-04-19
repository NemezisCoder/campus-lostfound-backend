from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_not_banned
from app.core.config import settings
from app.db.database import get_db
from app.db.models.stored_file import StoredFile
from app.db.models.user import User
from app.services.storage_s3 import delete_object, presign_get, upload_fileobj
from app.services.upload_validation import validate_image_upload

router = APIRouter(
    prefix="/media",
    tags=["media"],
)


def _build_misc_object_key(filename: str | None, content_type: str) -> str:
    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    ext = Path(filename or "").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ext_map.get(content_type, ".jpg")

    return f"misc/{uuid4().hex}{ext}"


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(require_not_banned),
    db: AsyncSession = Depends(get_db),
):
    size_bytes = await validate_image_upload(file)
    content_type = (file.content_type or "").lower()
    data = await file.read()

    object_key = _build_misc_object_key(file.filename, content_type)

    try:
        upload_fileobj(
            fileobj=data,
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
        kind="misc",
        owner_id=user.id,
        item_id=None,
    )

    db.add(stored)
    await db.commit()
    await db.refresh(stored)

    return {
        "id": stored.id,
        "filename": stored.original_name,
        "content_type": stored.content_type,
        "size_bytes": stored.size_bytes,
        "url": presign_get(stored.object_key),
    }


@router.get("/{file_id}/presign")
async def get_file_presigned_url(
    file_id: int,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(StoredFile).where(StoredFile.id == file_id))
    stored = res.scalar_one_or_none()

    if not stored:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "id": stored.id,
        "filename": stored.original_name,
        "url": presign_get(stored.object_key),
    }


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_file(
    file_id: int,
    user: User = Depends(require_not_banned),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(StoredFile).where(StoredFile.id == file_id))
    stored = res.scalar_one_or_none()

    if not stored:
        raise HTTPException(status_code=404, detail="File not found")

    is_admin = getattr(user, "is_admin", False)
    if stored.owner_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    try:
        delete_object(stored.object_key)
    except Exception:
        pass

    await db.delete(stored)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)