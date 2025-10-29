from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/items")

@router.get("")
def list_items(
    q: Optional[str] = Query(None, description="Поиск по названию/описанию"),
    status: Optional[str] = Query(None, description="lost|found|returned"),
    page: int = 1, size: int = 20
):
    return {"items": [], "page": page, "size": size}

@router.post("")
def create_item():
    return {"id": "demo"}

@router.get("/{item_id}")
def get_item(item_id: str):
    return {"id": item_id}

@router.patch("/{item_id}")
def update_item(item_id: str):
    return {"id": item_id, "updated": True}

@router.delete("/{item_id}")
def delete_item(item_id: str):
    return {"id": item_id, "deleted": True}
