from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid

from app.core.config import settings

router = APIRouter(
    prefix="/media",
    tags=["media"],
)
@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    ext = Path(file.filename or "").suffix.lower() or ".jpg"
    safe_ext = ext if ext in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"

    # Stored under MEDIA_DIR/misc/... and served via app.mount('/media', ...)
    rel_dir = Path("misc")
    abs_dir = Path(settings.MEDIA_DIR) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    name = f"{uuid.uuid4().hex}{safe_ext}"
    (abs_dir / name).write_bytes(data)

    return JSONResponse({"filename": file.filename, "url": f"/media/{rel_dir.as_posix()}/{name}"})
