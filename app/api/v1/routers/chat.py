# app/api/v1/routers/chat.py

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.item import Item
from app.db.models.chat_thread import ChatThread
from app.db.models.chat_message import ChatMessage

router = APIRouter(prefix="/chat", tags=["chat"])


class ThreadCreateIn(BaseModel):
    item_id: int
    peer_id: int


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
    created_at: str
    client_id: Optional[str] = None


def _now():
    return datetime.now(timezone.utc)


def _pair(me: int, peer: int) -> tuple[int, int]:
    return (min(me, peer), max(me, peer))


def _peer_for_me(t: ChatThread, me: int) -> int:
    return t.user_high_id if t.user_low_id == me else t.user_low_id


def _status_value(s):
    return getattr(s, "value", s)


@router.post("/thread", response_model=ThreadOut)
async def create_or_get_thread(
    payload: ThreadCreateIn,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
):
    if payload.peer_id == me.id:
        raise HTTPException(status_code=400, detail="Cannot chat with yourself")

    item = await db.scalar(select(Item).where(Item.id == payload.item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Можно чатиться только с владельцем объявления (или владелец может писать любому peer)
    if payload.peer_id != item.owner_id and me.id != item.owner_id:
        raise HTTPException(status_code=403, detail="You can chat only with item owner")

    lo, hi = _pair(me.id, payload.peer_id)

    # 1) Если thread уже существует для этой пары — возвращаем его
    existing = await db.scalar(
        select(ChatThread).where(
            ChatThread.item_id == payload.item_id,
            ChatThread.user_low_id == lo,
            ChatThread.user_high_id == hi,
        )
    )
    if existing:
        # backfill: если чат уже есть, но статус ещё OPEN — переведём в IN_PROGRESS
        if _status_value(item.status) == "OPEN":
            item.status = "IN_PROGRESS"
            await db.commit()

        return ThreadOut(
            id=existing.id,
            item_id=existing.item_id,
            peer_id=_peer_for_me(existing, me.id),
            item_title=item.title,
            item_status=_status_value(item.status),
            item_image_url=item.image_url,
            last_message_at=existing.last_message_at.isoformat() if existing.last_message_at else None,
            last_message_text=existing.last_message_text,
        )

    # 2) Если для item уже есть ЛЮБОЙ thread — третьим лицам запрещаем
    any_thread_id = await db.scalar(
        select(ChatThread.id).where(ChatThread.item_id == payload.item_id).limit(1)
    )
    if any_thread_id:
        raise HTTPException(status_code=409, detail="Chat already created for this item")

    # 3) Создаём первый thread и переводим item в IN_PROGRESS
    thread = ChatThread(
        item_id=payload.item_id,
        user_low_id=lo,
        user_high_id=hi,
        created_at=_now(),
        last_message_at=None,
        last_message_text=None,
    )
    db.add(thread)

    if _status_value(item.status) == "OPEN":
        item.status = "IN_PROGRESS"

    await db.commit()
    await db.refresh(thread)
    await db.refresh(item)

    return ThreadOut(
        id=thread.id,
        item_id=thread.item_id,
        peer_id=_peer_for_me(thread, me.id),
        item_title=item.title,
        item_status=_status_value(item.status),
        item_image_url=item.image_url,
        last_message_at=None,
        last_message_text=None,
    )


@router.get("/threads", response_model=List[ThreadOut])
async def list_threads(
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
):
    q = (
        select(ChatThread, Item.title, Item.status, Item.image_url)
        .join(Item, Item.id == ChatThread.item_id)
        .where(or_(ChatThread.user_low_id == me.id, ChatThread.user_high_id == me.id))
        .order_by(
            case((Item.status == "CLOSED", 1), else_=0).asc(),  # CLOSED вниз
            ChatThread.last_message_at.desc().nullslast(),
            ChatThread.created_at.desc(),
        )
    )

    rows = (await db.execute(q)).all()

    return [
        ThreadOut(
            id=t.id,
            item_id=t.item_id,
            peer_id=_peer_for_me(t, me.id),
            item_title=title,
            item_status=_status_value(status_),
            item_image_url=image_url,
            last_message_at=t.last_message_at.isoformat() if t.last_message_at else None,
            last_message_text=t.last_message_text,
        )
        for (t, title, status_, image_url) in rows
    ]


@router.post("/threads/{thread_id}/close", response_model=ThreadOut)
async def close_thread(
    thread_id: int,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
):
    thread = await db.scalar(select(ChatThread).where(ChatThread.id == thread_id))
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    if me.id not in (thread.user_low_id, thread.user_high_id):
        raise HTTPException(status_code=403, detail="Not your thread")

    item = await db.scalar(select(Item).where(Item.id == thread.item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # ✅ 1) ставим подтверждение от текущего юзера
    if me.id == thread.user_low_id:
        thread.close_low_confirmed = True
    else:
        thread.close_high_confirmed = True

    await db.commit()
    await db.refresh(thread)

    # ✅ 2) CLOSED только если подтвердили оба
    if thread.close_low_confirmed and thread.close_high_confirmed:
        if _status_value(item.status) != "CLOSED":
            item.status = "CLOSED"
            await db.commit()
            await db.refresh(item)

    return ThreadOut(
        id=thread.id,
        item_id=thread.item_id,
        peer_id=_peer_for_me(thread, me.id),
        item_title=item.title,
        item_status=_status_value(item.status),
        item_image_url=item.image_url,
        last_message_at=thread.last_message_at.isoformat() if thread.last_message_at else None,
        last_message_text=thread.last_message_text,
    )



@router.get("/threads/{thread_id}/messages", response_model=List[MessageOut])
async def list_messages(
    thread_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    me: User = Depends(get_current_user),
):
    thread = await db.scalar(select(ChatThread).where(ChatThread.id == thread_id))
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    if me.id not in (thread.user_low_id, thread.user_high_id):
        raise HTTPException(status_code=403, detail="Not your thread")

    q = (
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(min(limit, 200))
    )
    msgs = (await db.scalars(q)).all()

    return [
        MessageOut(
            id=m.id,
            thread_id=m.thread_id,
            sender_id=m.sender_id,
            text=m.text,
            created_at=m.created_at.isoformat(),
            client_id=m.client_id,
        )
        for m in msgs
    ]
