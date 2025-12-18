from datetime import datetime
from pydantic import BaseModel


class ThreadCreateRequest(BaseModel):
    item_id: int
    peer_id: int  # второй участник (не ты)


class ThreadOut(BaseModel):
    id: int
    item_id: int
    peer_id: int
    item_title: Optional[str] = None
    item_status: Optional[str] = None
    item_image_url: Optional[str] = None
    last_message_at: Optional[str] = None
    last_message_text: Optional[str] = None


class MessageOut(BaseModel):
    id: int
    thread_id: int
    sender_id: int
    text: str
    created_at: datetime
    client_id: str | None = None


class SendMessageRequest(BaseModel):
    text: str
    client_id: str | None = None
