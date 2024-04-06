from minio import Minio
from minio.error import S3Error

from app.config import settings

from app.config import log
from typing import Any

Clinet: Any

def connect_storage():
    global Clinet
    Clinet = Minio(
        settings.RESOURCE_ENDPOINT,
        access_key=settings.ACCESS_KEY,
        secret_key=settings.ACCESS_SECRET,
        region=settings.REGION,
        secure=False
    )
    # check if bucket exists
    if not Clinet.bucket_exists(settings.DEFAULT_BUCKET):
        try:
            Clinet.make_bucket(settings.DEFAULT_BUCKET)
        except S3Error as ex:
            log.error(f"failed to create bucket {ex}")
            raise ex

def get_client():
    return Clinet
