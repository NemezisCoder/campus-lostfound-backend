from app.db.database import Base, engine

from app.db.models.user import User  # noqa: F401
from app.db.models.refresh_token import RefreshToken  # noqa: F401


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
