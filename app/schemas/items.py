# app/schemas/items.py
from pydantic import BaseModel
from typing import Literal, Optional


ItemType = Literal["lost", "found"]
StatusType = Literal["OPEN", "IN_PROGRESS", "CLOSED"]
CategoryType = Literal["electronics", "clothes", "personal", "documents"]


class ItemBase(BaseModel):
    title: str
    type: ItemType
    status: StatusType
    category: CategoryType
    roomId: str
    roomLabel: str
    floorLabel: str
    timeAgo: str
    description: str


class ItemCreate(ItemBase):
    pass
    # если нужно – можно сделать timeAgo необязательным и
    # на бэке всегда ставить "только что"


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[StatusType] = None
    category: Optional[CategoryType] = None
    roomId: Optional[str] = None
    roomLabel: Optional[str] = None
    floorLabel: Optional[str] = None
    timeAgo: Optional[str] = None
    description: Optional[str] = None


class Item(ItemBase):
    id: int
    owner_id: int
