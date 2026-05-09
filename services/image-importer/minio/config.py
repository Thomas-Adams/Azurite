from minio import Minio
from minio.error import S3Error


MINIO_BUCKET_NAME= "tsukuyomi"
MINIO_ENDPOINT = "localhost:9001"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "12345678"
# Configure once at module level
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # True if using HTTPS
)
