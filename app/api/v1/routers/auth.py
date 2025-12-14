from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db.database import SessionLocal
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.auth.security import create_access_token, create_refresh_token
from app.auth.passwords import hash_password, verify_password
import os

IS_PROD = os.getenv("ENV") == "prod"

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_db():
    async with SessionLocal() as session:
        yield session


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    surname: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        name=payload.name,
        surname=payload.surname,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"id": user.id, "email": user.email, "name": user.name, "surname": user.surname}


@router.post("/login")
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(user.id)
    refresh = create_refresh_token()

    db.add(RefreshToken(token=refresh, user_id=user.id))
    await db.commit()

    response.set_cookie(
    key="refresh_token",
    value=refresh,
    httponly=True,
    samesite="none" if IS_PROD else "lax",
    secure=True if IS_PROD else False,
    path="/api/v1/auth/refresh",
)

    return {"access_token": access, "token_type": "bearer"}


@router.post("/refresh")
async def refresh(request: Request, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    session = await db.scalar(select(RefreshToken).where(RefreshToken.token == refresh_token))
    if not session:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access = create_access_token(session.user_id)
    return {"access_token": access, "token_type": "bearer"}


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await db.execute(delete(RefreshToken).where(RefreshToken.token == refresh_token))
        await db.commit()

    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")
    return {"ok": True}
