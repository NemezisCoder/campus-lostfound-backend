import time

from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.services.weather_service import weather_service

router = APIRouter(prefix="/weather", tags=["weather"])

_last_requests: dict[str, float] = {}


def check_weather_rate_limit(request: Request):
    if settings.APP_ENV == "development":
        return

    ip = request.client.host if request.client else "unknown"
    now = time.time()
    last = _last_requests.get(ip, 0)

    if now - last < 2:
        raise HTTPException(status_code=429, detail="Too many requests")

    _last_requests[ip] = now


@router.get("/campus")
async def get_campus_weather(request: Request):
    check_weather_rate_limit(request)

    try:
        return await weather_service.get_campus_weather()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail="Weather service is temporarily unavailable",
        ) from exc