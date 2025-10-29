from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.routers import items, auth, chat, media, search, status, health

app = FastAPI(title="Campus Lost&Found API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["auth"])
app.include_router(items.router, prefix=settings.API_V1_STR, tags=["items"])
app.include_router(status.router, prefix=settings.API_V1_STR, tags=["status"])
app.include_router(media.router, prefix=settings.API_V1_STR, tags=["media"])
app.include_router(search.router, prefix=settings.API_V1_STR, tags=["search"])
app.include_router(chat.router, prefix=settings.API_V1_STR, tags=["chat"])

@app.get("/", tags=["root"])
def root():
    return {"message": "Campus Lost&Found API is up", "api": settings.API_V1_STR}
