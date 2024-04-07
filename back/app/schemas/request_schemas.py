from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator
from decimal import Decimal


class UserCreate(BaseModel):
    """
    User create schema
    """

    email: EmailStr
    password: str
    username: str


class UserLogin(BaseModel):
    """
    User login schema
    """

    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """
    User update schema
    """

    email: Optional[EmailStr]
    password: Optional[str]
    username: Optional[str]

class UploadImage(BaseModel):
    """
    Image upload schema
    """

    description: Optional[str]
    metainfo: Optional[dict]
    tags: List[str]

class ImageCreate(BaseModel):
    """
    Image create schema
    """

    original_file_path: str
    thumbnail_file_path: str
    description: Optional[str]
    exif: dict
    metainfo: Optional[dict]
    tags: List[str]

class UserStoreCreate(BaseModel):
    """
    User store create schema
    """

    store_name: str
