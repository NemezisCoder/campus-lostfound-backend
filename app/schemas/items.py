from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


ItemType = Literal["lost", "found"]
StatusType = Literal["OPEN", "IN_PROGRESS", "CLOSED"]
CategoryType = Literal["electronics", "clothes", "personal", "documents"]
ItemSort = Literal["id_desc", "id_asc", "title_asc", "title_desc"]


class ItemBase(BaseModel):
    title: str = Field(..., max_length=120)
    type: ItemType
    category: CategoryType
    roomId: str = Field(..., max_length=50)
    roomLabel: str = Field(..., max_length=120)
    floorLabel: str = Field(..., max_length=50)
    timeAgo: str = Field(..., max_length=50)
    description: str = Field(..., max_length=2000)
    image_url: Optional[str] = Field(default=None, max_length=1000)


class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    type: ItemType
    category: CategoryType
    roomId: str = Field(..., min_length=1, max_length=50)
    roomLabel: str = Field(..., min_length=1, max_length=120)
    floorLabel: str = Field(..., min_length=1, max_length=50)
    timeAgo: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=2000)
    image_url: Optional[str] = Field(default=None, max_length=1000)


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    status: Optional[StatusType] = None
    category: Optional[CategoryType] = None
    roomId: Optional[str] = Field(default=None, min_length=1, max_length=50)
    roomLabel: Optional[str] = Field(default=None, min_length=1, max_length=120)
    floorLabel: Optional[str] = Field(default=None, min_length=1, max_length=50)
    timeAgo: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    image_url: Optional[str] = Field(default=None, max_length=1000)


class Item(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    status: StatusType


class ItemsQuery(BaseModel):
    q: Optional[str] = Field(default=None, max_length=80)
    type: Optional[ItemType] = None
    status: Optional[StatusType] = None
    category: Optional[CategoryType] = None
    sort: ItemSort = "id_desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=50)


class ItemsPage(BaseModel):
    items: list[Item]
    total: int
    page: int
    page_size: int


class SimilarItemMatch(BaseModel):
    item: Item
    similarity: float


class SimilarByImageResponse(BaseModel):
    matches: list[SimilarItemMatch]


class DeduplicateResponse(BaseModel):
    possible_duplicates: list[SimilarItemMatch]