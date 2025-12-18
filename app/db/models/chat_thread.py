from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ChatThread(Base):
    __tablename__ = "chat_threads"

    id: Mapped[int] = mapped_column(primary_key=True)

    # чат всегда привязан к item
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)

    # храним участников в отсортированном виде (low/high), чтобы уникальность была простой
    user_low_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user_high_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_message_text: Mapped[str | None] = mapped_column(String, nullable=True)

    # ✅ подтверждения закрытия (2 шага)
    close_low_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    close_high_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("item_id", "user_low_id", "user_high_id", name="uq_thread_item_users"),
    )

    messages = relationship("ChatMessage", back_populates="thread", cascade="all, delete-orphan")
