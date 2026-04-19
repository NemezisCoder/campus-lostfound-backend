from fastapi import HTTPException, UploadFile

from app.core.config import settings


async def validate_image_upload(file: UploadFile) -> int:
    content_type = (file.content_type or "").lower()

    if content_type not in settings.allowed_image_mime_set:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}",
        )

    total_size = 0
    chunk_size = 1024 * 1024  # 1 MB

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break

        total_size += len(chunk)

        if total_size > settings.max_upload_size_bytes:
            await file.seek(0)
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size is {settings.MAX_UPLOAD_SIZE_MB} MB",
            )

    await file.seek(0)

    if total_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file",
        )

    return total_size