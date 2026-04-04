from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Здесь теперь будет храниться hash refresh token, а не raw token
    token: Mapped[str] = mapped_column(String, unique=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Идентификатор "семьи" refresh-токенов для rotation/replay detection
    session_id: Mapped[str] = mapped_column(String, index=True, default="")

    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )