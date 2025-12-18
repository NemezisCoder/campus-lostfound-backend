import asyncio
from sqlalchemy import text
from app.db.database import SessionLocal

ITEM_ID = 4  # <-- подставь id объявления

async def main():
    async with SessionLocal() as db:
        item = (await db.execute(
            text("select id, status from items where id=:id"), {"id": ITEM_ID}
        )).all()

        threads = (await db.execute(
            text("select id, item_id, user_low_id, user_high_id from chat_threads where item_id=:id"),
            {"id": ITEM_ID}
        )).all()

        print("ITEM:", item)
        print("THREADS:", threads)

asyncio.run(main())
