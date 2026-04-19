from functools import lru_cache
from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings


S3_CONFIG = Config(
    signature_version="s3v4",
    s3={"addressing_style": "path"},
)


def _ensure_s3_enabled() -> None:
    if not settings.S3_ENABLED:
        raise RuntimeError("S3 is disabled")


@lru_cache
def s3_internal() -> BaseClient:
    _ensure_s3_enabled()
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_INTERNAL_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
        config=S3_CONFIG,
    )


@lru_cache
def s3_external_signer() -> BaseClient:
    _ensure_s3_enabled()
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_EXTERNAL_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
        config=S3_CONFIG,
    )


def upload_fileobj(
    fileobj: bytes | BinaryIO,
    object_key: str,
    content_type: str,
) -> None:
    if isinstance(fileobj, bytes):
        fileobj = BytesIO(fileobj)

    try:
        s3_internal().upload_fileobj(
            Fileobj=fileobj,
            Bucket=settings.S3_BUCKET,
            Key=object_key,
            ExtraArgs={"ContentType": content_type},
        )
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"S3 upload failed: {e}") from e


def delete_object(object_key: str) -> None:
    try:
        s3_internal().delete_object(
            Bucket=settings.S3_BUCKET,
            Key=object_key,
        )
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"S3 delete failed: {e}") from e


def presign_get(object_key: str) -> str:
    try:
        return s3_external_signer().generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": settings.S3_BUCKET,
                "Key": object_key,
            },
            ExpiresIn=settings.PRESIGN_EXPIRES_SECONDS,
        )
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"S3 presign failed: {e}") from e