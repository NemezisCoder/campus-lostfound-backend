from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.routers import items, auth, chat, media, search, status, health
from app.db.init_db import init_db

from pathlib import Path
from app.core.config import settings

app = FastAPI(title="Campus Lost&Found API", version="0.1.0")

# Serve uploaded images in dev. In production you likely want MinIO/S3 + CDN.
app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

origins = settings.CORS_ORIGINS or default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["set-cookie"],
)

app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(items.router, prefix=settings.API_V1_STR)
app.include_router(status.router, prefix=settings.API_V1_STR)
app.include_router(media.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)


@app.get("/", tags=["root"])
def root():
    return {"message": "Campus Lost&Found API is up", "api": settings.API_V1_STR}


@app.on_event("startup")
async def startup():
    await init_db()

print("DATABASE_URL =", settings.DATABASE_URL)
print("CWD =", Path.cwd())
print("DB FILE ABS =", (Path.cwd() / "app.db").resolve())