# app/api/v1/routers/items.py
from fastapi import APIRouter, HTTPException, status
from typing import List

from app.schemas.items import Item, ItemCreate, ItemUpdate

router = APIRouter(
    prefix="/items",   
    tags=["items"],
)

# Простая "фейковая БД" в памяти — этого достаточно для ЛР4
FAKE_ITEMS: List[Item] = []


def _get_next_id() -> int:
    if not FAKE_ITEMS:
        return 1
    return max(item.id for item in FAKE_ITEMS) + 1


@router.get("/", response_model=List[Item])
def list_items() -> List[Item]:
    return FAKE_ITEMS


@router.get("/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    for item in FAKE_ITEMS:
        if item.id == item_id:
            return item
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Item not found",
    )


@router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate) -> Item:
    new_item = Item(
        id=_get_next_id(),
        **payload.model_dump(),
    )
    FAKE_ITEMS.append(new_item)
    return new_item


@router.patch("/{item_id}", response_model=Item)
def update_item(item_id: int, payload: ItemUpdate) -> Item:
    for index, item in enumerate(FAKE_ITEMS):
        if item.id == item_id:
            data = payload.model_dump(exclude_unset=True)
            updated = item.model_copy(update=data)
            FAKE_ITEMS[index] = updated
            return updated

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Item not found",
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    for index, item in enumerate(FAKE_ITEMS):
        if item.id == item_id:
            FAKE_ITEMS.pop(index)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Item not found",
    )
