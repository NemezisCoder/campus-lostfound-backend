from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.config import settings


async def migrate_sqlite(conn: AsyncConnection) -> None:
    """Idempotent SQLite schema migration.

    Your project uses Base.metadata.create_all() on startup.
    That creates missing tables but does NOT add columns to existing tables.
    For SQLite dev setups, we patch the schema with ALTER TABLE if needed.
    """

    if not str(settings.DATABASE_URL).startswith("sqlite"):
        return

    # If users table doesn't exist yet, create_all will create it with new columns.
    rows = (
        await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        )
    ).fetchall()
    if not rows:
        return

    cols = (await conn.execute(text("PRAGMA table_info(users)"))).fetchall()
    colnames = {c[1] for c in cols}  # column name is index 1

    if "role" not in colnames:
        await conn.execute(
            text("ALTER TABLE users ADD COLUMN role VARCHAR NOT NULL DEFAULT 'user'")
        )
    if "is_banned" not in colnames:
        await conn.execute(
            text("ALTER TABLE users ADD COLUMN is_banned INTEGER NOT NULL DEFAULT 0")
        )
