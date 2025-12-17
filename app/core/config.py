from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    APP_ENV: str = "development"
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DB_PATH: Path = BASE_DIR / "db.sqlite3"
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_PATH.as_posix()}"

    MEDIA_DIR: str = str(BASE_DIR / "uploads")

    class Config:
        env_file = str(BASE_DIR / ".env")

settings = Settings()

Path(settings.MEDIA_DIR).mkdir(parents=True, exist_ok=True)
