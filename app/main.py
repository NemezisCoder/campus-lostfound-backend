from pathlib import Path

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import PlainTextResponse, Response

from app.api.v1.routers import admin, auth, chat, health, items, media, search, status
from app.api.v1.routers.weather import router as weather_router
from app.core.config import settings
from app.db.init_db import init_db
from app.realtime.socketio_server import sio


fastapi_app = FastAPI(title="Campus Lost&Found API", version="0.1.0")

fastapi_app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
    compresslevel=5,
)

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

origins = settings.CORS_ORIGINS or default_origins

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["set-cookie"],
)

fastapi_app.include_router(health.router, prefix=settings.API_V1_STR)
fastapi_app.include_router(auth.router, prefix=settings.API_V1_STR)
fastapi_app.include_router(items.router, prefix=settings.API_V1_STR)
fastapi_app.include_router(status.router, prefix=settings.API_V1_STR)
fastapi_app.include_router(media.router, prefix=settings.API_V1_STR)
fastapi_app.include_router(search.router, prefix=settings.API_V1_STR)
fastapi_app.include_router(chat.router, prefix=settings.API_V1_STR)
fastapi_app.include_router(admin.router, prefix=settings.API_V1_STR)
fastapi_app.include_router(weather_router, prefix=settings.API_V1_STR)


@fastapi_app.get("/", tags=["root"])
def root():
    return {"message": "Campus Lost&Found API is up", "api": settings.API_V1_STR}


@fastapi_app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    return f"""User-agent: *
Allow: /
Disallow: /api/
Disallow: /socket.io/
Disallow: /admin
Disallow: /chat
Disallow: /create
Disallow: /profile
Disallow: /account
Disallow: /login
Disallow: /register
Disallow: /forgot
Sitemap: {settings.SITE_BASE_URL}/sitemap.xml
"""


@fastapi_app.get("/sitemap.xml", response_class=Response)
async def sitemap_xml():
    base_url = settings.SITE_BASE_URL

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
  </url>
</urlset>
"""
    return Response(content=xml, media_type="application/xml")


@fastapi_app.on_event("startup")
async def startup():
    await init_db()


app = socketio.ASGIApp(
    sio,
    other_asgi_app=fastapi_app,
    socketio_path="socket.io",
)

print("DATABASE_URL =", settings.DATABASE_URL)
print("CWD =", Path.cwd())