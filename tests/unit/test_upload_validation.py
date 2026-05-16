import io

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.services.upload_validation import validate_image_upload


def make_upload_file(content: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(content),
        filename="test.jpg",
        headers=Headers({"content-type": content_type}),
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_image_upload_accepts_jpeg():
    file = make_upload_file(
        b"fake image bytes",
        "image/jpeg",
    )

    result = await validate_image_upload(file)

    assert result == len(b"fake image bytes")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_image_upload_rejects_unsupported_type():
    file = make_upload_file(
        b"not image",
        "text/plain",
    )

    with pytest.raises(Exception):
        await validate_image_upload(file)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_image_upload_rejects_empty_file():
    file = make_upload_file(
        b"",
        "image/png",
    )

    with pytest.raises(Exception):
        await validate_image_upload(file)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_image_upload_resets_seek_position():
    file = make_upload_file(
        b"fake image bytes",
        "image/png",
    )

    await validate_image_upload(file)

    assert file.file.tell() == 0