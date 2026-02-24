from sqlalchemy import String, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    surname: Mapped[str] = mapped_column(String)

    # RBAC + moderation flags
    role: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="user",
        server_default=text("'user'"),
    )
    is_banned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
    )
    
    items = relationship("Item", back_populates="owner")