from typing import Optional, List, Dict, Union
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
from decimal import Decimal


class UploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    message: str
    full_path: str
    thumbnail_path: str
    embed: List
    similar_image_pth: Optional[str]

class Token(BaseModel):
    access_token: str
    token_type: str

class ProcessingInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    message: str


class TokenData(BaseModel):
    email: str | None = None


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str

class Image(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_file_path: str
    thumbnail_file_path: str
    description: str
    exif: str
    metainfo: Dict

    @field_validator('exif', mode='before')
    def validate_exif(cls, value):
        return str(value)
class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_file_path: str
    thumbnail_file_path: str
    description: str
    exif: str
    metainfo: Dict

class ImageListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    count: int
    images: List[ImageResponse]

class ImageList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    images: List[Image]

class Tag(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

class TagList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    tags: List[Tag]

class UserStore(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    store_name: str

class UserStoreList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    user_stores: List[UserStore]