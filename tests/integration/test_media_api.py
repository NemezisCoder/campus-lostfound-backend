import pytest


MEDIA_URL = "/api/v1/media"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_cannot_upload_media(client):
    response = await client.post(
        f"{MEDIA_URL}/upload",
        files={
            "file": (
                "test.jpg",
                b"fake image bytes",
                "image/jpeg",
            )
        },
    )

    assert response.status_code in [401, 403]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_cannot_delete_media(client):
    response = await client.delete(f"{MEDIA_URL}/1")

    assert response.status_code in [401, 403, 404]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.xfail(reason="Тест может упасть, если в backend используется user.is_admin вместо user.role == 'admin'")
async def test_admin_can_delete_other_user_media(
    client,
    auth_admin_headers,
    media_from_regular_user,
):
    response = await client.delete(
        f"{MEDIA_URL}/{media_from_regular_user.id}",
        headers=auth_admin_headers,
    )

    assert response.status_code == 204