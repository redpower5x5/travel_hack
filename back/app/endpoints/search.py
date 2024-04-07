from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status, Query

from sqlalchemy.orm import Session

from app.config import log
from app.schemas import response_schemas
from app.core.dependencies import get_db
from app.click.dependencies import get_click
from app.click.vector_utils import cosine_compare, get_image_vector
from app.core import crud
from app.config import settings
from app.utils.token import get_current_active_user, get_current_active_admin
from base64 import b64encode
from fastapi_cache.decorator import cache
from typing import List
import numpy as np
import requests
import time

router = APIRouter(
    prefix="/search",
    tags=["search"],
)

def get_propper_probalities(data):

    response = []
    probs = np.array([1-elem[1] for elem in data])
    #first range
    i = 0
    top_one = probs[(probs >= 0.9) & (probs < 0.98)]
    if top_one.shape[0] != 0:
        response.append(data[i + top_one.argmax()])
    i += top_one.shape[0]
    r = min(0.9, data[0][1])
    step = 0.01
    while len(response) < 5 and r - step > 0.65:
        top_one = probs[(probs >= r - step) & (probs < r)]
        if top_one.shape[0] != 0:
            response.append(data[i + top_one.argmax()])
            r = top_one.max() - 0.015
        else:
            r -= step
        i += top_one.shape[0]
    return response
# get all tags
@router.get("/tags", response_model=response_schemas.TagList)
@cache(expire=settings.CACHE_EXPIRE)
async def get_tags(
    db: Session = Depends(get_db),
):
    """
    Get all tags
    """
    tags = crud.get_all_tags(db=db)

    if tags is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tags found",
        )

    return tags

# get all images with pagination
@router.get("/images", response_model=response_schemas.ImageListResponse)
# @cache(expire=settings.CACHE_EXPIRE)
async def get_images(
    page: int = Query(1),
    per_page: int = Query(10),
    db: Session = Depends(get_db),
):
    """
    Get all images with pagination
    """
    images = crud.get_all_images(db=db, page=page, per_page=per_page)

    if images is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No images found",
        )

    return images

# get all images by tags and/or search string
@router.get("/images/search", response_model=response_schemas.ImageList)
# @cache(expire=settings.CACHE_EXPIRE)
async def search_images(
    tags: List[str] = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
    click = Depends(get_click),
):
    """
    Get all images by tags and/or search string
    """
    if tags is None:
        tags = []
    if search is None:
        search = ""
    if search == "" and len(tags) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tags and search string",
        )
    if search:
        log.debug(f"searching images by {search}")
        # search images via clickhouse
        # first, get text embedding via nuclio
        response = requests.post(
            settings.NUCLIO_API_URL,
            json={"mode": "text", "texts": [search]},
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
        # search images via clickhouse
        click_respone = cosine_compare(click, embed)
        log.debug(f"search response {click_respone}")
        image_ids_search = [int(row[0]) for row in click_respone]
        images_search: response_schemas.ImageList = crud.get_images_by_ids(db=db, image_ids=image_ids_search)
    if tags:
        images_tags: response_schemas.ImageList = crud.get_images_with_tags(db=db, tags=tags)
    if search and tags:
        # merge two classes, preserve ids from tags
        images_list = []
        for image in images_tags.images:
            if image.id in image_ids_search:
                images_list.append(image)
        images = response_schemas.ImageList(
            count=len(images_list),
            images=images_list,
        )
        return images
    if search:
        return images_search
    if tags:
        return images_tags

    if images is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No images found",
        )

# find similar image by uploaded image
@router.post("/images/similar", response_model=response_schemas.ImageList)
# @cache(expire=settings.CACHE_EXPIRE)
async def find_similar_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    click = Depends(get_click),
):
    """
    Find similar image by uploaded image
    """
    try:
        encoded_image = b64encode(file.file.read()).decode()
        # get image embedding via nuclio
        response = requests.post(
            settings.NUCLIO_API_URL,
            json={"mode": "image", "image": encoded_image},
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
        # find similar images via clickhouse
        click_respone = cosine_compare(click, embed, limit=False)
        log.debug(f"click embeed output: {click_respone}")
        # get top 5 images
        click_respone = get_propper_probalities(click_respone)
        image_ids = [int(row[0]) for row in click_respone]
        images: response_schemas.ImageList = crud.get_images_by_ids(db=db, image_ids=image_ids)
        return images
    except Exception as ex:
        log.error(f"failed to find similar image {ex.with_traceback()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar image",
        )

# seearch by image id
@router.get("/images/{image_id}", response_model=response_schemas.ImageResponse)
# @cache(expire=settings.CACHE_EXPIRE)
async def get_image_by_id(
    image: int,
    db: Session = Depends(get_db),
):
    """
    Get image by id
    """
    image = crud.get_image_by_id(db=db, image_id=image)

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    return image

# search similar images to given image id
@router.get("/images/{image_id}/similar", response_model=response_schemas.ImageList)
# @cache(expire=settings.CACHE_EXPIRE)
async def get_similar_images(
    image_id: int,
    db: Session = Depends(get_db),
    click = Depends(get_click),
):
    """
    Get similar images to given image id
    """
    # get image vector from clickhouse
    image_vector = get_image_vector(client=click, image_id=image_id)
    # find similar images via clickhouse
    click_respone = cosine_compare(click, image_vector)
    log.debug(f"click embeed output: {click_respone}")
    # get top 5 images
    click_respone = get_propper_probalities(click_respone)
    image_ids = [int(row[0]) for row in click_respone]
    images: response_schemas.ImageList = crud.get_images_by_ids(db=db, image_ids=image_ids)
    return images