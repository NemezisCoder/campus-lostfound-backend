from app.db.database import Base, engine
from app.db.models.item import Item
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
