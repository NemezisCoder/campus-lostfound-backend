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

    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="items")

    stored_files = relationship(
        "StoredFile",
        back_populates="item",
        cascade="all, delete-orphan",
    )