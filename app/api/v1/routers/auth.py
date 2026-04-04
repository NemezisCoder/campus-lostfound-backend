from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.passwords import hash_password
from app.auth.repository import RefreshTokenRepository, UserRepository
from app.auth.service import AuthService
from app.core.config import settings
from app.db.database import get_db
from app.db.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    surname: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    surname: str
    role: str
    is_banned: bool


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(
        users=UserRepository(db),
        refresh_tokens=RefreshTokenRepository(db),
        refresh_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        revoke_old_sessions_on_login=settings.REVOKE_OLD_SESSIONS_ON_LOGIN,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        name=payload.name,
        surname=payload.surname,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "surname": user.surname,
    }


@router.post("/login", response_model=TokenPairOut)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
):
    tokens = await svc.login(payload.email, payload.password)
    await db.commit()

    return TokenPairOut(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=TokenPairOut)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
):
    tokens = await svc.refresh(payload.refresh_token)
    await db.commit()

    return TokenPairOut(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="bearer",
    )


@router.post("/logout")
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    svc: AuthService = Depends(get_auth_service),
):
    await svc.logout(payload.refresh_token)
    await db.commit()

    return {"ok": True}


@router.get("/me", response_model=MeOut)
async def me(current_user: User = Depends(get_current_user)):
    return MeOut(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        surname=current_user.surname,
        role=getattr(current_user, "role", "user"),
        is_banned=getattr(current_user, "is_banned", False),
    )