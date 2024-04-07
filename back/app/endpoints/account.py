from fastapi import APIRouter, Depends, HTTPException, status, File
from sqlalchemy import CursorResult

from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from app.config import log
from app.schemas import response_schemas, request_schemas
from app.core.dependencies import get_db
from app.core import crud
from app.config import settings
from app.utils.token import get_current_active_user, get_current_active_admin

from fastapi_cache.decorator import cache

import time

router = APIRouter(
    prefix="/account",
    tags=["account"],
)

# add userStore to user
@router.post("/store/add", response_model=response_schemas.UserStore)
async def add_user_store(
    user_store: request_schemas.UserStoreCreate,
    db: Session = Depends(get_db),
    current_user: response_schemas.User = Depends(get_current_active_user),
):
    """
    Add user store
    """
    user_store = crud.create_user_store(db=db, user=current_user, store_name=user_store.store_name)

    return user_store

# edit user store
@router.post("/store/{id}/edit", response_model=response_schemas.UserStore)
async def edit_user_store(
    id: int,
    user_store: request_schemas.UserStoreEdit,
    db: Session = Depends(get_db),
    current_user: response_schemas.User = Depends(get_current_active_user)
):
    """
    Edit user store
    """
    user_store = crud.update_user_store(db=db, user=current_user, store_id=id, store_name=user_store.store_name)

    return user_store


# get usere stores
@router.get("/store/all", response_model=response_schemas.UserStoreList)
async def get_user_stores(
    db: Session = Depends(get_db),
    current_user: response_schemas.User = Depends(get_current_active_user),
):
    """
    Get user stores
    """
    user_stores = crud.get_all_user_stores(db=db, user=current_user)
    if user_stores is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user stores found",
        )

    return user_stores

# get user store images
@router.get("/store/{id}", response_model=response_schemas.ImageList)
async def get_user_store_images(
    id: int,
    db: Session = Depends(get_db),
    current_user: response_schemas.User = Depends(get_current_active_user),
):
    """
    Get user store images
    """
    images = crud.get_all_images_from_user_store(db=db, user=current_user, store_id=id)

    return images

# add images to user store
@router.post("/store/{id}/add")
async def add_image_to_user_store(
    id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: response_schemas.User = Depends(get_current_active_user),
):
    """
    Add image to user store
    """
    user_store = crud.add_image_to_user_store(db=db, user=current_user, store_id=id, image_id=image_id)

    return user_store
