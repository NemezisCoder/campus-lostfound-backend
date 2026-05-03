import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import settings


class WeatherService:
    def __init__(self) -> None:
        self._cache_data: dict[str, Any] | None = None
        self._cache_expires_at: datetime | None = None

    def _is_cache_valid(self) -> bool:
        if self._cache_data is None or self._cache_expires_at is None:
            return False
        return datetime.now(timezone.utc) < self._cache_expires_at

    def _normalize(self, payload: dict[str, Any], *, cached: bool) -> dict[str, Any]:
        weather_list = payload.get("weather") or []
        main = payload.get("main") or {}
        wind = payload.get("wind") or {}

        weather = weather_list[0] if weather_list else {}

        return {
            "provider": "openweathermap",
            "location": {
                "lat": payload.get("coord", {}).get("lat", settings.CAMPUS_LAT),
                "lon": payload.get("coord", {}).get("lon", settings.CAMPUS_LON),
            },
            "temp_c": main.get("temp"),
            "feels_like_c": main.get("feels_like"),
            "humidity": main.get("humidity"),
            "wind_mps": wind.get("speed"),
            "summary": weather.get("description"),
            "icon": weather.get("icon"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "cached": cached,
        }

    async def _fetch_from_openweather(self) -> dict[str, Any]:
        if not settings.OPENWEATHER_API_KEY:
            raise RuntimeError("OPENWEATHER_API_KEY is not configured")

        url = settings.OPENWEATHER_BASE_URL
        params = {
            "lat": settings.CAMPUS_LAT,
            "lon": settings.CAMPUS_LON,
            "appid": settings.OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "ru",
        }

        timeout = httpx.Timeout(connect=3.0, read=5.0, write=5.0, pool=3.0)

        last_error: Exception | None = None

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(0.5 * (attempt + 1))
                else:
                    break

        raise RuntimeError("Failed to fetch weather from OpenWeatherMap") from last_error

    async def get_campus_weather(self) -> dict[str, Any]:
        if self._is_cache_valid():
            cached_payload = dict(self._cache_data or {})
            cached_payload["cached"] = True
            return cached_payload

        raw = await self._fetch_from_openweather()
        normalized = self._normalize(raw, cached=False)

        self._cache_data = normalized
        self._cache_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.WEATHER_CACHE_SECONDS
        )

        return normalized


weather_service = WeatherService()