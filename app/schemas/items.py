from pydantic import BaseModel
from typing import Optional, List

class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "lost"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photos: List[str] = []
