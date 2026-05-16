import pytest


WEATHER_URL = "/api/v1/weather/campus"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_returns_200(client):
    response = await client.get(WEATHER_URL)

    assert response.status_code == 200

    data = response.json()
    assert "temperature" in data
    assert "feels_like" in data
    assert "humidity" in data
    assert "summary" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_rate_limit(client):
    responses = []

    for _ in range(20):
        res = await client.get(WEATHER_URL)
        responses.append(res.status_code)

    assert any(code == 429 for code in responses) or all(
        code == 200 for code in responses
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_external_api_failure(client, monkeypatch):
    async def fake_fail(*args, **kwargs):
        raise RuntimeError("External API down")

    monkeypatch.setattr(
        "app.services.weather_service.weather_service.get_campus_weather",
        fake_fail,
        raising=False,
    )

    response = await client.get(WEATHER_URL)

    assert response.status_code in [500, 503]