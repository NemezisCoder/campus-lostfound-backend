import os

import pytest
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager

os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["OPENWEATHER_API_KEY"] = "test-weather-key"

from app.main import app


@pytest.fixture(autouse=True)
def clear_global_state(monkeypatch):
    """
    Подменяем внешние сервисы между тестами:
    - S3-хранилище;
    - генерацию ссылок на изображения;
    - CLIP/open_clip embeddings;
    - OpenWeatherMap.
    """

    def fake_upload_fileobj(*args, **kwargs):
        return None

    def fake_delete_object(*args, **kwargs):
        return None

    def fake_presign_get(*args, **kwargs):
        return "https://example.com/fake-image.jpg"

    def fake_embed_image_bytes(*args, **kwargs):
        return [0.1, 0.2, 0.3]

    async def fake_get_campus_weather(*args, **kwargs):
        return {
            "provider": "test",
            "city": "Campus",
            "temperature": 20,
            "feels_like": 20,
            "humidity": 50,
            "wind_speed": 1,
            "summary": "clear",
            "icon": "01d",
        }

    monkeypatch.setattr(
        "app.services.storage_s3.upload_fileobj",
        fake_upload_fileobj,
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.storage_s3.delete_object",
        fake_delete_object,
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.storage_s3.presign_get",
        fake_presign_get,
        raising=False,
    )
    monkeypatch.setattr(
        "app.ai.embeddings.embed_image_bytes",
        fake_embed_image_bytes,
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.weather_service.weather_service.get_campus_weather",
        fake_get_campus_weather,
        raising=False,
    )


@pytest.fixture
async def client():
    async with LifespanManager(app):
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as ac:
            yield ac