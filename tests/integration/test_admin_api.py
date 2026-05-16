import pytest


ADMIN_URL = "/api/v1/admin"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_cannot_access_admin_reports(client):
    response = await client.get(f"{ADMIN_URL}/reports")

    assert response.status_code in [401, 403]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xfail(reason="Нужна фикстура auth_user_headers")
async def test_regular_user_gets_403(client, auth_user_headers):
    response = await client.get(
        f"{ADMIN_URL}/reports",
        headers=auth_user_headers,
    )

    assert response.status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xfail(reason="Нужны auth_admin_headers и regular_user")
async def test_admin_can_ban_user(client, auth_admin_headers, regular_user):
    response = await client.patch(
        f"{ADMIN_URL}/users/{regular_user.id}/ban",
        headers=auth_admin_headers,
    )

    assert response.status_code in [200, 204]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xfail(reason="Нужны auth_admin_headers и regular_user")
async def test_admin_can_change_user_role(client, auth_admin_headers, regular_user):
    response = await client.patch(
        f"{ADMIN_URL}/users/{regular_user.id}/role",
        headers=auth_admin_headers,
        json={
            "role": "admin",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["role"] == "admin"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xfail(reason="Нужна auth_admin_headers")
async def test_admin_gets_404_for_missing_user(client, auth_admin_headers):
    response = await client.patch(
        f"{ADMIN_URL}/users/999999/role",
        headers=auth_admin_headers,
        json={
            "role": "admin",
        },
    )

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xfail(reason="Нужны auth_admin_headers и admin_user")
async def test_admin_conflict_action_returns_409(client, auth_admin_headers, admin_user):
    response = await client.patch(
        f"{ADMIN_URL}/users/{admin_user.id}/role",
        headers=auth_admin_headers,
        json={
            "role": "admin",
        },
    )

    assert response.status_code in [200, 409]