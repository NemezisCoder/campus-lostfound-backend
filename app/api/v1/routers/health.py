import asyncio

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.services import storage_s3

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("")
def health():
    return {"ok": True}


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    checks = {
        "database": "unknown",
        "storage": "disabled" if not settings.S3_ENABLED else "unknown",
    }

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except SQLAlchemyError as exc:
        checks["database"] = "error"
        raise HTTPException(status_code=503, detail=checks) from exc

    if settings.S3_ENABLED:
        try:
            await asyncio.to_thread(
                storage_s3.s3_internal().head_bucket,
                Bucket=settings.S3_BUCKET,
            )
            checks["storage"] = "ok"
        except (BotoCoreError, ClientError, RuntimeError) as exc:
            checks["storage"] = "error"
            raise HTTPException(status_code=503, detail=checks) from exc

    return {"ok": True, "checks": checks}
