from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.auth.service import AuthService


class FakeUserRepo:
    def __init__(self):
        self.user = SimpleNamespace(
            id=1,
            email="user@test.com",
            hashed_password="hashed-password",
            is_active=True,
        )

    async def find_by_email(self, email: str):
        if email == self.user.email:
            return self.user
        return None

    async def get_by_email(self, email: str):
        return await self.find_by_email(email)


class FakeRefreshTokenRepo:
    def __init__(self):
        self.tokens = {}
        self.created = []
        self.revoked_families = []
        self.revoked_users = []

    async def find_by_token_value(self, token_value: str):
        return self.tokens.get(token_value)

    async def revoke_all_for_user(self, user_id: int):
        self.revoked_users.append(user_id)

    async def revoke_family(self, session_id: str):
        self.revoked_families.append(session_id)
        for token in self.tokens.values():
            if token.session_id == session_id:
                token.revoked_at = datetime.utcnow()

    async def revoke_by_token_value(self, token_value: str):
        token = self.tokens.get(token_value)
        if token:
            token.revoked_at = datetime.utcnow()

    async def create(self, **kwargs):
        token = SimpleNamespace(
            id=len(self.created) + 1,
            user_id=kwargs["user_id"],
            token=kwargs.get("token") or kwargs.get("token_value"),
            session_id=kwargs["session_id"],
            expires_at=kwargs["expires_at"],
            revoked_at=None,
            last_used_at=None,
        )
        self.tokens[token.token] = token
        self.created.append(token)
        return token


def make_service():
    users = FakeUserRepo()
    refresh_tokens = FakeRefreshTokenRepo()

    service = AuthService(
        users=users,
        refresh_tokens=refresh_tokens,
        refresh_days=30,
        revoke_old_sessions_on_login=True,
    )

    return service, users, refresh_tokens


@pytest.fixture(autouse=True)
def patch_auth_dependencies(monkeypatch):
    refresh_values = iter(["refresh-1", "refresh-2", "refresh-3"])

    def fake_verify_password(password: str, hashed_password: str) -> bool:
        return password == "correct-password"

    def fake_create_access_token(*args, **kwargs) -> str:
        return "access-token"

    def fake_new_refresh_token() -> str:
        return next(refresh_values)

    def fake_hash_refresh_token(token: str) -> str:
        return f"hashed-{token}"

    monkeypatch.setattr(
        "app.auth.service.verify_password",
        fake_verify_password,
        raising=False,
    )
    monkeypatch.setattr(
        "app.auth.service.create_access_token",
        fake_create_access_token,
        raising=False,
    )
    monkeypatch.setattr(
        "app.auth.service.new_refresh_token",
        fake_new_refresh_token,
        raising=False,
    )
    monkeypatch.setattr(
        "app.auth.service.hash_refresh_token",
        fake_hash_refresh_token,
        raising=False,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_success():
    service, users, refresh_tokens = make_service()

    result = await service.login(
        email="user@test.com",
        password="correct-password",
    )

    assert result.access_token == "access-token"
    assert result.refresh_token == "refresh-1"
    assert len(refresh_tokens.created) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_rejects_invalid_password():
    service, users, refresh_tokens = make_service()

    with pytest.raises(HTTPException):
        await service.login(
            email="user@test.com",
            password="wrong-password",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_token_rotation():
    service, users, refresh_tokens = make_service()

    login_result = await service.login(
        email="user@test.com",
        password="correct-password",
    )

    refresh_result = await service.refresh(login_result.refresh_token)

    assert refresh_result.access_token == "access-token"
    assert refresh_result.refresh_token == "refresh-2"
    assert len(refresh_tokens.created) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_rejects_expired_token():
    service, users, refresh_tokens = make_service()

    expired_token = SimpleNamespace(
        id=1,
        user_id=1,
        token="hashed-expired-refresh",
        session_id="session-1",
        expires_at=datetime.utcnow() - timedelta(days=1),
        revoked_at=None,
        last_used_at=None,
    )

    refresh_tokens.tokens["hashed-expired-refresh"] = expired_token

    with pytest.raises(HTTPException):
        await service.refresh("expired-refresh")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_rejects_revoked_token_replay():
    service, users, refresh_tokens = make_service()

    revoked_token = SimpleNamespace(
        id=1,
        user_id=1,
        token="hashed-revoked-refresh",
        session_id="session-1",
        expires_at=datetime.utcnow() + timedelta(days=1),
        revoked_at=datetime.utcnow(),
        last_used_at=None,
    )

    refresh_tokens.tokens["hashed-revoked-refresh"] = revoked_token

    with pytest.raises(HTTPException):
        await service.refresh("revoked-refresh")

    assert "session-1" in refresh_tokens.revoked_families


@pytest.mark.unit
@pytest.mark.asyncio
async def test_logout_revokes_refresh_token_family():
    service, users, refresh_tokens = make_service()

    login_result = await service.login(
        email="user@test.com",
        password="correct-password",
    )

    await service.logout(login_result.refresh_token)

    assert len(refresh_tokens.revoked_families) == 1