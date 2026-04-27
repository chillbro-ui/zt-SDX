import boto3

from app.core.config import settings


s3 = boto3.client(
    "s3",
    endpoint_url=f"http://{settings.MINIO_HOST}:{settings.MINIO_PORT}",
    aws_access_key_id=settings.MINIO_ROOT_USER,
    aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
)


def ensure_bucket() -> None:
    existing = [b["Name"] for b in s3.list_buckets()["Buckets"]]

    if settings.MINIO_BUCKET not in existing:
        s3.create_bucket(Bucket=settings.MINIO_BUCKET)