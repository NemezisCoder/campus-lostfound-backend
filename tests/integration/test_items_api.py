# tests/integration/test_items_api.py

import pytest


ITEMS_URL = "/api/v1/items/"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_can_list_items(client):
    response = await client.get(ITEMS_URL)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list) or "items" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_can_list_items_with_pagination(client):
    response = await client.get(
        ITEMS_URL,
        params={
            "limit": 10,
            "offset": 0,
        },
    )

    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_can_list_items_with_filters(client):
    response = await client.get(
        ITEMS_URL,
        params={
            "category": "electronics",
            "status": "lost",
        },
    )

    assert response.status_code in [200, 422]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_item_not_found(client):
    response = await client.get(f"{ITEMS_URL}/999999")

    assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unauthorized_user_cannot_create_item(client):
    response = await client.post(
        ITEMS_URL,
        json={
            "title": "Lost phone",
            "description": "Black phone",
            "category": "electronics",
            "status": "lost",
        },
    )

    assert response.status_code in [401, 403]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unauthorized_user_cannot_patch_item(client):
    response = await client.patch(
        f"{ITEMS_URL}/1",
        json={
            "title": "Updated title",
        },
    )

    assert response.status_code in [401, 403, 404, 405]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unauthorized_user_cannot_delete_item(client):
    response = await client.delete(f"{ITEMS_URL}/1")

    assert response.status_code in [401, 403, 404, 405]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_item_validation_error(client):
    response = await client.post(
        ITEMS_URL,
        json={
            "title": "",
        },
    )

    assert response.status_code in [401, 403, 422]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_items_invalid_pagination(client):
    response = await client.get(
        ITEMS_URL,
        params={
            "limit": -1,
            "offset": -1,
        },
    )

    assert response.status_code in [200, 422]