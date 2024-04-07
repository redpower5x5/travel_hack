from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, File, UploadFile, Form

from sqlalchemy.orm import Session

from app.config import log
from app.schemas import response_schemas, request_schemas
from app.core.dependencies import get_db
from app.s3.storage import get_client
from app.click.dependencies import get_click
from app.click.vector_utils import check_if_similar, add_image, cosine_compare
from minio import Minio
from uuid import uuid4
from base64 import urlsafe_b64encode, b64encode
from app.core import crud
from app.config import settings
import requests
import asyncio
import os
import json
from io import BytesIO
from PIL import Image
from PIL import ExifTags

router = APIRouter(
    prefix="/uploader",
    tags=["uploader"],
)

def base64UrlEncode(data):
    return urlsafe_b64encode(data).rstrip(b'=')

@router.post("/upload", response_model=response_schemas.UploadResponse)
def upload_file(
    background_tasks: BackgroundTasks,
    description: str = Form(...),
    metainfo: str = Form(...),
    tags: list[str] = Form(...),
    file: UploadFile = File(...),
    client: Minio = Depends(get_client),
    session: Session = Depends(get_db),
    click_clinet = Depends(get_click),
    ):
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
        full_path = f"{settings.S3_ENDPOINT}/{settings.DEFAULT_BUCKET}/{object_name}"
        s3_url = f"s3://{settings.DEFAULT_BUCKET}/{object_name}"
        imgproxy_objeect_name_base = base64UrlEncode(s3_url.encode('utf-8')).decode('utf-8')

        # create thumbnail via imgproxy
        # save aspect ratio, do not crop, try to resize to 700x700 pixels, saving in png format
        thumbnail_path_imgproxy = f"{settings.IMGPROXY_HOST}/unsafe/rs:fit:700:700/{imgproxy_objeect_name_base}.png"
        model_ready_imgproxy = f"{settings.IMGPROXY_HOST}/unsafe/rs:force:288:288/{imgproxy_objeect_name_base}.png"
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
        thumbnail_path = f"{settings.S3_ENDPOINT}/{settings.DEFAULT_BUCKET}/{thumbnail_object_name}"
        client.put_object(settings.DEFAULT_BUCKET, thumbnail_object_name, raw_thumbnail, raw_thumbnail_len)

        response = requests.get(model_ready_imgproxy)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get model_ready image",
            )
        encoded_image_ready = b64encode(response.content).decode()
        response = requests.post(
            settings.NUCLIO_API_URL,
            json={"mode": "image", "image": encoded_image_ready},
            headers={"Content-Type": "application/json",
                     "x-nuclio-function-name": "clip-function",
                     "x-nuclio-function-namespace": "nuclio"}
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get model_ready image",
            )
        embed = response.json()["embed"][0]

        # save to db and click
        # extract exif from image
        img = Image.open(file.file)
        exif = { ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS }
        # save to db
        image = crud.create_image(session, request_schemas.ImageCreate(
            original_file_path=full_path,
            thumbnail_file_path=thumbnail_path,
            description=description,
            exif=exif,
            metainfo=json.loads(metainfo),
            tags=tags[0].split(',')
        ))
        # check if similar image exists
        res = check_if_similar(click_clinet, embed)
        # find most similar image
        most_sim = cosine_compare(click_clinet, embed)
        # save to clickhouse
        add_image(click_clinet, image.id, embed, [0])
        log.debug(f"Similar image found: {res}")
        if res:
            log.info(f"Similar image found: {res}")
            # get path to similar image
            image_similar = crud.get_image_by_id(session, int(res[0][0]))
            # get tags of similar image
            tags_similar = crud.get_tags_of_image(session, image_similar.id)
            return response_schemas.UploadResponse(
                status="success",
                message="file uploaded",
                image_id=image.id,
                full_path=full_path,
                thumbnail_path=thumbnail_path,
                embed=embed,
                similar_image_pth=image_similar.thumbnail_file_path,
                suggested_tags=tags_similar
            )
        else:
            if len(most_sim) > 0:
                image_similar = crud.get_image_by_id(session, int(most_sim[0][0]))
                # get tags of similar image
                tags_similar = crud.get_tags_of_image(session, image_similar.id)
            else:
                tags_similar = response_schemas.TagList(count=0, tags=[])
            # return response
            return response_schemas.UploadResponse(
                status="success",
                message="file uploaded",
                full_path=full_path,
                thumbnail_path=thumbnail_path,
                embed=embed,
                similar_image_pth="no",
                suggested_tags=tags_similar
            )
    except Exception as ex:
        log.error(f"failed to upload file {ex.with_traceback()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file",
        )

# Delete image
@router.delete("/delete/{image_id}", response_model=response_schemas.ProcessingInfo)
def delete_image(
    image_id: int,
    client: Minio = Depends(get_client),
    session: Session = Depends(get_db),
    click_clinet = Depends(get_click),
    ):
    """Delete image from S3

    Args:
        image_id (int): [description]
        client (Minio, optional): [description]. Defaults to Depends(get_client).

    Raises:
        HTTPException: [description]

    Returns:
        [type]: [description]
    """
    try:
        # get image from db
        image = crud.get_image_by_id(session, image_id)
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )
        # delete image from clickhouse
        click_clinet.command(f"ALTER TABLE images DELETE WHERE id = {image_id}")
        # delete image from db
        crud.delete_image(session, image_id)
        # delete image from s3
        client.remove_object(settings.DEFAULT_BUCKET, image.original_file_path.split('/')[-1])
        client.remove_object(settings.DEFAULT_BUCKET, image.thumbnail_file_path.split('/')[-1])
        return response_schemas.ProcessingInfo(
            status="success",
            message="Image deleted",
        )
    except Exception as ex:
        log.error(f"failed to delete image {ex.with_traceback()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image",
        )