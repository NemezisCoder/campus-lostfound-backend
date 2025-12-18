from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional

ItemType = Literal["lost", "found"]
StatusType = Literal["OPEN", "IN_PROGRESS", "CLOSED"]
CategoryType = Literal["electronics", "clothes", "personal", "documents"]


class ItemBase(BaseModel):
    title: str
    type: ItemType
    category: CategoryType
    roomId: str
    roomLabel: str
    floorLabel: str
    timeAgo: str
    description: str
    image_url: Optional[str] = None


class ItemCreate(ItemBase):
    """Client cannot set status; server sets it to OPEN."""
    pass


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    status: Optional[StatusType] = None
    category: Optional[CategoryType] = None
    roomId: Optional[str] = None
    roomLabel: Optional[str] = None
    floorLabel: Optional[str] = None
    timeAgo: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class Item(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    status: StatusType


class SimilarItemMatch(BaseModel):
    item: Item
    similarity: float


class SimilarByImageResponse(BaseModel):
    matches: list[SimilarItemMatch]


class DeduplicateResponse(BaseModel):
    possible_duplicates: list[SimilarItemMatch]
