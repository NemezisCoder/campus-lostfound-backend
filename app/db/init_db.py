from app.db.database import Base, engine
import app.db.models  # side-effect import: регистрирует модели в Base.metadata

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
