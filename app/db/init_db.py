from app.db.database import Base, engine
import app.db.models  # side-effect import: регистрирует модели в Base.metadata
from app.db.migrate_sqlite import migrate_sqlite

async def init_db():
    async with engine.begin() as conn:
        await migrate_sqlite(conn)
        await conn.run_sync(Base.metadata.create_all)
