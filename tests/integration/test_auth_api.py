import pytest


AUTH_LOGIN_URL = "/api/v1/auth/login"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_missing_email(client):
    response = await client.post(
        AUTH_LOGIN_URL,
        json={"password": "password123"},
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_missing_password(client):
    response = await client.post(
        AUTH_LOGIN_URL,
        json={"email": "user@test.com"},
    )

    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_invalid_password(client):
    response = await client.post(
        AUTH_LOGIN_URL,
        json={
            "email": "user@test.com",
            "password": "wrong",
        },
    )

    assert response.status_code in [401, 404]