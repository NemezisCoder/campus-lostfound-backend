from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)

    roomId: Mapped[str] = mapped_column(String, nullable=False)
    roomLabel: Mapped[str] = mapped_column(String, nullable=False)
    floorLabel: Mapped[str] = mapped_column(String, nullable=False)
    timeAgo: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    # Optional media / AI fields (MVP)
    # `image_url` is a link to the stored image (local StaticFiles in dev; S3/MinIO in prod).
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    # `embedding` is a list[float] stored as JSON for MVP (SQLite-compatible).
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="items")