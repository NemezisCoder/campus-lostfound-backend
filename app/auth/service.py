from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid

from fastapi import HTTPException, status

from app.auth.passwords import verify_password
from app.auth.security import create_access_token
from app.auth.token_store import new_refresh_token, hash_refresh_token
from app.auth.repository import UserRepository, RefreshTokenRepository


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepository,
        refresh_tokens: RefreshTokenRepository,
        refresh_days: int,
        revoke_old_sessions_on_login: bool,
    ):
        self.users = users
        self.refresh_tokens = refresh_tokens
        self.refresh_days = max(1, int(refresh_days))
        self.revoke_old_sessions_on_login = revoke_old_sessions_on_login

    def _now(self) -> datetime:
        return datetime.utcnow()

    def _refresh_expires_at(self, now: datetime) -> datetime:
        return now + timedelta(days=self.refresh_days)

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if self.revoke_old_sessions_on_login:
            await self.refresh_tokens.revoke_all_for_user(user.id)

        now = self._now()
        access = create_access_token(user.id)

        raw_refresh = new_refresh_token()
        token_hash = hash_refresh_token(raw_refresh)
        session_id = str(uuid.uuid4())

        await self.refresh_tokens.create(
            user_id=user.id,
            token_value=token_hash,
            session_id=session_id,
            created_at=now,
            expires_at=self._refresh_expires_at(now),
        )

        return TokenPair(
            access_token=access,
            refresh_token=raw_refresh,
        )

    async def refresh(self, raw_refresh: str | None) -> TokenPair:
        if not raw_refresh:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No refresh token",
            )

        now = self._now()
        presented_hash = hash_refresh_token(raw_refresh)

        row = await self.refresh_tokens.find_by_token_value(presented_hash)
        if not row:
            row = await self.refresh_tokens.find_by_token_value(raw_refresh)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        if row.revoked_at is not None:
            if row.session_id:
                await self.refresh_tokens.revoke_family(row.session_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token replay detected",
            )

        if not row.expires_at or row.expires_at < now:
            row.revoked_at = now
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        row.last_used_at = now
        row.revoked_at = now

        session_id = row.session_id or str(uuid.uuid4())
        row.session_id = session_id

        access = create_access_token(row.user_id)

        new_raw = new_refresh_token()
        new_hash = hash_refresh_token(new_raw)

        await self.refresh_tokens.create(
            user_id=row.user_id,
            token_value=new_hash,
            session_id=session_id,
            created_at=now,
            expires_at=self._refresh_expires_at(now),
        )

        return TokenPair(
            access_token=access,
            refresh_token=new_raw,
        )

    async def logout(self, raw_refresh: str | None) -> None:
        if not raw_refresh:
            return

        presented_hash = hash_refresh_token(raw_refresh)

        row = await self.refresh_tokens.find_by_token_value(presented_hash)
        if not row:
            row = await self.refresh_tokens.find_by_token_value(raw_refresh)

        if not row:
            return

        if row.session_id:
            await self.refresh_tokens.revoke_family(row.session_id)
        else:
            row.revoked_at = self._now()