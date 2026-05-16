import pytest

from app.services.weather_service import WeatherService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_weather_cache_miss(monkeypatch):
    service = WeatherService()

    calls = 0

    async def fake_fetch_from_openweather():
        nonlocal calls
        calls += 1
        return {
            "weather": [{"description": "clear", "icon": "01d"}],
            "main": {
                "temp": 20,
                "feels_like": 19,
                "humidity": 50,
            },
            "wind": {"speed": 2},
            "name": "Test City",
        }

    monkeypatch.setattr(
        service,
        "_fetch_from_openweather",
        fake_fetch_from_openweather,
    )

    result = await service.get_campus_weather()

    assert calls == 1
    assert result["summary"] == "clear"
    assert result["temp_c"] == 20
    assert result["feels_like_c"] == 19
    assert result["humidity"] == 50
    assert result["cached"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_weather_cache_hit(monkeypatch):
    service = WeatherService()

    calls = 0

    async def fake_fetch_from_openweather():
        nonlocal calls
        calls += 1
        return {
            "weather": [{"description": "clear", "icon": "01d"}],
            "main": {
                "temp": 20,
                "feels_like": 19,
                "humidity": 50,
            },
            "wind": {"speed": 2},
            "name": "Test City",
        }

    monkeypatch.setattr(
        service,
        "_fetch_from_openweather",
        fake_fetch_from_openweather,
    )

    first = await service.get_campus_weather()
    second = await service.get_campus_weather()

    assert calls == 1

    assert first["summary"] == second["summary"]
    assert first["temp_c"] == second["temp_c"]
    assert first["feels_like_c"] == second["feels_like_c"]
    assert first["humidity"] == second["humidity"]

    assert first["cached"] is False
    assert second["cached"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_weather_external_api_error(monkeypatch):
    service = WeatherService()

    async def fake_fetch_from_openweather():
        raise RuntimeError("Failed to fetch weather from OpenWeatherMap")

    monkeypatch.setattr(
        service,
        "_fetch_from_openweather",
        fake_fetch_from_openweather,
    )

    with pytest.raises(RuntimeError):
        await service.get_campus_weather()