from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.db.scalar(
            select(User).where(User.email == email)
        )

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.db.scalar(
            select(User).where(User.id == user_id)
        )


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_token_value(self, token_value: str) -> Optional[RefreshToken]:
        return await self.db.scalar(
            select(RefreshToken).where(RefreshToken.token == token_value)
        )

    async def revoke_family(self, session_id: str) -> None:
        if not session_id:
            return

        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.session_id == session_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.utcnow())
        )

    async def revoke_all_for_user(self, user_id: int) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.utcnow())
        )

    async def create(
        self,
        *,
        user_id: int,
        token_value: str,
        session_id: str,
        created_at: datetime,
        expires_at: datetime,
    ) -> RefreshToken:
        row = RefreshToken(
            user_id=user_id,
            token=token_value,
            session_id=session_id,
            created_at=created_at,
            expires_at=expires_at,
            revoked_at=None,
            last_used_at=None,
        )
        self.db.add(row)
        return row