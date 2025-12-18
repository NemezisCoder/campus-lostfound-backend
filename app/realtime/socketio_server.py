from datetime import datetime
import socketio
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.auth.security import ALGORITHM
from app.db.database import SessionLocal
from app.db.models.chat_thread import ChatThread
from app.db.models.chat_message import ChatMessage

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.CORS_ORIGINS,
)

def room_name(thread_id: int) -> str:
    return f"thread:{thread_id}"

async def _get_db() -> AsyncSession:
    async with SessionLocal() as s:
        yield s

@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token")
    if not token:
        return False

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            return False
        user_id = int(sub)
    except (JWTError, ValueError):
        return False

    await sio.save_session(sid, {"user_id": user_id})
    return True

@sio.event
async def disconnect(sid):
    # ничего не нужно
    return

@sio.on("chat:join")
async def chat_join(sid, data):
    thread_id = int((data or {}).get("threadId") or 0)
    if not thread_id:
        return

    session = await sio.get_session(sid)
    me_id = int(session["user_id"])

    async with SessionLocal() as db:
        thread = await db.scalar(select(ChatThread).where(ChatThread.id == thread_id))
        if not thread:
            return

        if me_id not in (thread.user_low_id, thread.user_high_id):
            return

        await sio.enter_room(sid, room_name(thread_id))

        # отправим историю (последние 50)
        rows = (await db.execute(
            select(ChatMessage)
            .where(ChatMessage.thread_id == thread_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(50)
        )).scalars().all()

        rows = list(reversed(rows))
        await sio.emit("chat:history", {
            "threadId": thread_id,
            "messages": [
                {
                    "id": m.id,
                    "threadId": m.thread_id,
                    "senderId": m.sender_id,
                    "text": m.text,
                    "createdAt": m.created_at.isoformat(),
                    "clientId": m.client_id,
                } for m in rows
            ]
        }, to=sid)

@sio.on("chat:message")
async def chat_message(sid, data):
    thread_id = int((data or {}).get("threadId") or 0)
    text = str((data or {}).get("text") or "").strip()
    client_id = (data or {}).get("clientId")

    if not thread_id or not text:
        return

    session = await sio.get_session(sid)
    me_id = int(session["user_id"])

    async with SessionLocal() as db:
        thread = await db.scalar(select(ChatThread).where(ChatThread.id == thread_id))
        if not thread:
            return
        if me_id not in (thread.user_low_id, thread.user_high_id):
            return

        msg = ChatMessage(
            thread_id=thread_id,
            sender_id=me_id,
            text=text,
            client_id=client_id,
            created_at=datetime.utcnow(),
        )
        db.add(msg)

        thread.last_message_at = msg.created_at
        thread.last_message_text = msg.text

        await db.commit()
        await db.refresh(msg)

        payload = {
            "id": msg.id,
            "threadId": thread_id,
            "senderId": me_id,
            "text": msg.text,
            "createdAt": msg.created_at.isoformat(),
            "clientId": msg.client_id,
        }
        await sio.emit("chat:message", payload, to=room_name(thread_id))
