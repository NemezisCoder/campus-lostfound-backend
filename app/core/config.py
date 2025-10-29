from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    APP_ENV: str = "development"
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = "sqlite:///./app.db"
    MEDIA_DIR: str = "./uploads"

    class Config:
        env_file = ".env"

settings = Settings()
os.makedirs(settings.MEDIA_DIR, exist_ok=True)
