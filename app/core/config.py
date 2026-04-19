from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        extra="ignore",
    )

    # === Server ===
    APP_ENV: str = "development"
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SITE_BASE_URL: str = "http://localhost:8000"

    # === CORS ===
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    # === Security ===
    SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # === Refresh token policy ===
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REVOKE_OLD_SESSIONS_ON_LOGIN: bool = True

    # === DB ===
    POSTGRES_DB: str = "campus"
    POSTGRES_USER: str = "campus"
    POSTGRES_PASSWORD: str = "campus123"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://campus:campus123@db:5432/campus"

    # === Optional local media fallback ===
    MEDIA_DIR: str = str(BASE_DIR / "uploads")

    # === Weather ===
    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    CAMPUS_LAT: float = 55.6700
    CAMPUS_LON: float = 37.6500
    WEATHER_CACHE_SECONDS: int = 300

    # === S3 / MinIO ===
    S3_ENABLED: bool = True
    S3_BUCKET: str = "campus-lostfound"
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin123"
    S3_INTERNAL_ENDPOINT: str = "http://minio:9000"
    S3_EXTERNAL_ENDPOINT: str = "http://localhost:9000"

    PRESIGN_EXPIRES_SECONDS: int = 600
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_IMAGE_MIME: str = "image/jpeg,image/png,image/webp"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def allowed_image_mime_set(self) -> set[str]:
        return {
            item.strip()
            for item in self.ALLOWED_IMAGE_MIME.split(",")
            if item.strip()
        }


settings = Settings()