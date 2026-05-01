from io import BytesIO

from minio import Minio

from app.core.config import settings


client = Minio(
    endpoint=f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
    access_key=settings.MINIO_ROOT_USER,
    secret_key=settings.MINIO_ROOT_PASSWORD,
    secure=False,
)

# Use bucket name from config — not hardcoded
BUCKET = settings.MINIO_BUCKET


def ensure_bucket():
    if not client.bucket_exists(BUCKET):
        client.make_bucket(BUCKET)


def upload_file(object_name: str, content: bytes, content_type: str):
    data = BytesIO(content)
    client.put_object(
        bucket_name=BUCKET,
        object_name=object_name,
        data=data,
        length=len(content),
        content_type=content_type,
    )


def get_download_url(object_name: str) -> str:
    return client.presigned_get_object(BUCKET, object_name)


def get_file_bytes(object_name: str) -> bytes:
    """Fetch raw bytes from MinIO — used for decryption and DLP scanning."""
    response = client.get_object(BUCKET, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()
