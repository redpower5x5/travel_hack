from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from datetime import datetime

from typing import Union

from app.models import db_models, models
from app.schemas import response_schemas, request_schemas
from app.config import log
from app.utils.token import get_password_hash
from app.utils.next_week import get_next_week_dates
import os

from typing import List


def get_user(db: Session, email: Union[str, None]) -> Union[models.UserInDB, None]:
    try:
        user = (
            db.query(db_models.User)
            .filter(
                db_models.User.email == email,
            )
            .one()
        )
        user = models.UserInDB(
            id=user.id,
            email=user.email,
            username=user.username,
            hashed_password=user.hashed_password,
        )
        return user
    except NoResultFound:
        return None
def check_if_user_admin(db: Session, user: response_schemas.User) -> bool:
    try:
        result = (
            db.query(db_models.User)
            .filter_by(
                id=user.id,
                role=db_models.Role.admin,
            ).first()
        )
        return result is not None
    except NoResultFound:
        return False

def create_user(db: Session, user: request_schemas.UserCreate) -> response_schemas.User:
    db_user = db_models.User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    db_user = response_schemas.User.model_validate(db_user)

    log.info(f"Created user: {db_user}")
    return db_user

def user_update(db: Session,
                user: request_schemas.UserUpdate,
                current_user: response_schemas.User
                ) -> Union[response_schemas.User, None]:
    try:
        db_user = (
            db.query(db_models.User)
            .filter(
                db_models.User.id == current_user.id,
            )
            .one()
        )
        if user.email:
            db_user.email = user.email
        if user.username:
            db_user.username = user.username
        if user.password:
            db_user.hashed_password = get_password_hash(user.password)
        db.commit()
        db.refresh(db_user)


        db_user = response_schemas.User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
        )

        log.info(f"Updated user {db_user}")
        return db_user

    except NoResultFound:
        return None

def create_image(db: Session, image: request_schemas.ImageCreate) -> response_schemas.Image:
    """create image in db. assign tags to image. create tags if not exist"""
    try:
        db_image = db_models.Image(
            original_file_path=image.original_file_path,
            thumbnail_file_path=image.thumbnail_file_path,
            description=image.description,
            exif=image.exif,
            metainfo=image.metainfo,
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)

        tags = []
        for tag_name in image.tags:
            try:
                db_tag = (
                    db.query(db_models.Tag)
                    .filter(
                        db_models.Tag.name == tag_name,
                    )
                    .one()
                )
            except NoResultFound:
                db_tag = db_models.Tag(
                    name=tag_name,
                )
                db.add(db_tag)
                db.commit()
                db.refresh(db_tag)
            tags.append(db_tag)
        db_image.tags = tags
        db.commit()
        db.refresh(db_image)

        db_image = response_schemas.Image.model_validate(db_image)

        log.info(f"Created image: {db_image}")
        return db_image

    except NoResultFound:
        return None

def get_all_tags(db: Session) -> response_schemas.TagList:
    try:
        tags = (
            db.query(db_models.Tag)
            .all()
        )
        tags = [response_schemas.Tag.model_validate(tag) for tag in tags]
        return response_schemas.TagList(
            count=len(tags),
            tags=tags,
        )
    except NoResultFound:
        return response_schemas.TagList(
            count=0,
            tags=[],
        )

def get_images_with_tags(db: Session, tags: List[str]) -> response_schemas.ImageList:
    try:
        images = (
            db.query(db_models.Image)
            .join(db_models.Image.tags)
            .filter(
                db_models.Tag.name.in_(tags),
            )
            .all()
        )
        images = [response_schemas.Image.model_validate(image) for image in images]
        return response_schemas.ImageList(
            count=len(images),
            images=images,
        )
    except NoResultFound:
        return response_schemas.ImageList(
            count=0,
            images=[],
        )

def get_images_by_ids(db: Session, image_ids: List[int]) -> response_schemas.ImageList:
    try:
        images = (
            db.query(db_models.Image)
            .filter(
                db_models.Image.id.in_(image_ids),
            )
            .all()
        )
        images = [response_schemas.Image.model_validate(image) for image in images]

        return response_schemas.ImageList(
            count=len(images),
            images=images,
        )
    except NoResultFound:
        return response_schemas.ImageList(
            count=0,
            images=[],
        )

def get_all_images(db: Session, page: int, per_page: int) -> response_schemas.ImageListResponse:
    try:
        total_count = len(
            db.query(db_models.Image)
            .all()
        )
        images = (
            db.query(db_models.Image)
            .limit(per_page)
            .offset((page - 1) * per_page)
            .all()
        )
        images_list = [response_schemas.Image.model_validate(image) for image in images]
        return response_schemas.ImageList(
            count=total_count,
            images=images_list,
        )
    except NoResultFound:
        return response_schemas.ImageList(
            count=0,
            images=[],
        )

def get_image_by_id(db: Session, image_id: int) -> Union[response_schemas.Image, None]:
    try:
        image = (
            db.query(db_models.Image)
            .filter(
                db_models.Image.id == image_id,
            )
            .one()
        )
        image = response_schemas.Image.model_validate(image)
        return image
    except NoResultFound:
        return None

def get_tags_of_image(db: Session, image_id: int) -> response_schemas.TagList:
    try:
        tags = (
            db.query(db_models.Tag)
            .join(db_models.Image.tags)
            .filter(
                db_models.Image.id == image_id,
            )
            .all()
        )
        tags = [response_schemas.Tag.model_validate(tag) for tag in tags]
        return response_schemas.TagList(
            count=len(tags),
            tags=tags,
        )
    except NoResultFound:
        return response_schemas.TagList(
            count=0,
            tags=[],
        )

def delete_image(db: Session, image_id: int) -> None:
    """delete image from db. delte from ImageTag table as well"""
    try:
        db.query(db_models.ImageTag).filter(db_models.ImageTag.image_id == image_id).delete()
        db.query(db_models.Image).filter(db_models.Image.id == image_id).delete()
        db.commit()
    except NoResultFound:
        pass

def get_all_user_stores(db: Session, user: response_schemas.User) -> response_schemas.UserStoreList:
    try:
        stores = (
            db.query(db_models.UserStore)
            .filter(
                db_models.UserStore.user_id == user.id,
            )
            .all()
        )
        stores_list = [response_schemas.UserStore.model_validate(store) for store in stores]
        return response_schemas.UserStoreList(
            count=len(stores),
            user_stores=stores_list,
        )
    except NoResultFound:
        return None

def create_user_store(db: Session, user: response_schemas.User, store_name: str) -> response_schemas.UserStore:
    try:
        db_store = db_models.UserStore(
            user_id=user.id,
            store_name=store_name,
        )
        db.add(db_store)
        db.commit()
        db.refresh(db_store)

        db_store = response_schemas.UserStore.model_validate(db_store)

        log.info(f"Created store: {db_store}")
        return db_store

    except NoResultFound:
        return None

def update_user_store(db: Session, user: response_schemas.User, store_id: int, store_name: str) -> response_schemas.UserStore:
    try:
        db_store = (
            db.query(db_models.UserStore)
            .filter(
                db_models.UserStore.id == store_id,
                db_models.UserStore.user_id == user.id,
            )
            .one()
        )
        db_store.store_name = store_name
        db.commit()
        db.refresh(db_store)

        db_store = response_schemas.UserStore.model_validate(db_store)

        log.info(f"Updated store: {db_store}")
        return db_store

    except NoResultFound:
        return None

def add_image_to_user_store(db: Session, user: response_schemas.User, store_id: int, image_id: int) -> response_schemas.UserStore:
    try:
        db_store = db_models.UserImageStore(
            store_id=store_id,
            image_id=image_id,
        )
        db.add(db_store)
        db.commit()
        db.refresh(db_store)

        db_store = {"added": True, "store_id": store_id, "image_id": image_id}

        log.info(f"Added image to store: {db_store}")
        return db_store

    except NoResultFound:
        return None

def get_all_images_from_user_store(db: Session, user: response_schemas.User, store_id: int) -> response_schemas.ImageList:
    try:
        rows = (
            db.query(db_models.UserImageStore)
            .filter(
                db_models.UserImageStore.store_id == store_id,
            )
            .all()
        )
        images = [row.image for row in rows]
        images = [response_schemas.Image.model_validate(image) for image in images]
        return response_schemas.ImageList(
            count=len(images),
            images=images,
        )
    except NoResultFound:
        return response_schemas.ImageList(
            count=0,
            images=[],
        )