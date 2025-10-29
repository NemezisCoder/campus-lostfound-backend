from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/media")

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    return JSONResponse({"filename": file.filename, "url": f"/media/{file.filename}"})
