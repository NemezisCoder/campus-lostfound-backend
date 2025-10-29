from fastapi import APIRouter, UploadFile, File
from typing import List

router = APIRouter(prefix="/search")

@router.post("/similar-by-image")
async def similar_by_image(file: UploadFile = File(...)):
    return {"similar_items": []}

@router.post("/deduplicate")
async def deduplicate(items: List[str]):
    return {"duplicates": []}
