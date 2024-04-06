from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, File, UploadFile

from sqlalchemy.orm import Session

from app.config import log
from app.schemas import response_schemas, request_schemas
# from app.core.dependencies import get_db
from app.s3.storage import get_client
from minio import Minio
from uuid import uuid4
from base64 import urlsafe_b64encode
# from app.core import crud
from app.config import settings
import requests
import asyncio
import os
from io import BytesIO

router = APIRouter(
    prefix="/uploader",
    tags=["uploader"],
)

def base64UrlEncode(data):
    return urlsafe_b64encode(data).rstrip(b'=')

@router.post("/upload", response_model=response_schemas.UploadResponse)
def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    client: Minio = Depends(get_client)):
    """Upload file to S3

    Args:
        background_tasks (BackgroundTasks): [description]
        file (UploadFile, optional): [description]. Defaults to File(...).
        client (Minio, optional): [description]. Defaults to Depends(get_client).

    Raises:
        HTTPException: [description]

    Returns:
        [type]: [description]
    """
    # check file extension is image
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed",
        )
    try:
        # save file to minio with uuid as object name
        object_name = f"{uuid4()}.{file.filename.split('.')[-1]}"
        client.put_object(settings.DEFAULT_BUCKET, object_name, file.file, file.size)
        full_path = f"{settings.RESOURCE_ENDPOINT}/{settings.DEFAULT_BUCKET}/{object_name}"
        s3_url = f"s3://{settings.DEFAULT_BUCKET}/{object_name}"
        imgproxy_objeect_name_base = base64UrlEncode(s3_url.encode('utf-8')).decode('utf-8')

        # create thumbnail via imgproxy
        # save aspect ratio, do not crop, try to resize to 700x700 pixels, saving in png format
        thumbnail_path_imgproxy = f"{settings.IMGPROXY_HOST}/unsafe/rs:fit:700:700/{imgproxy_objeect_name_base}.png"
        # get thumbnail image with get request
        response = requests.get(thumbnail_path_imgproxy)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get thumbnail",
            )
        response_bytes = response.content
        raw_thumbnail = BytesIO(response_bytes)
        raw_thumbnail_len = raw_thumbnail.getbuffer().nbytes
        #save to minio
        thumbnail_object_name = f"t{object_name.split('.')[0]}-thumb.png"
        thumbnail_path = f"{settings.RESOURCE_ENDPOINT}/{settings.DEFAULT_BUCKET}/{thumbnail_object_name}"
        client.put_object(settings.DEFAULT_BUCKET, thumbnail_object_name, raw_thumbnail, raw_thumbnail_len)

        # return response
        return response_schemas.UploadResponse(
            status="success",
            message="file uploaded",
            full_path=full_path,
            thumbnail_path=thumbnail_path
        )
    except Exception as ex:
        log.error(f"failed to upload file {ex}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file",
        )

