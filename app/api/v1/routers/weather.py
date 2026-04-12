from fastapi import APIRouter, HTTPException

from app.services.weather_service import weather_service

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/campus")
async def get_campus_weather():
    try:
        return await weather_service.get_campus_weather()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail="Weather service is temporarily unavailable",
        ) from exc