from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Enum,
    UniqueConstraint,
    TEXT,
    Numeric,
    Boolean,
    PickleType
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    hashed_password = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now())

class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.now())

class Image(Base):
    __tablename__ = "image"
    id = Column(Integer, primary_key=True)
    original_file_path = Column(String(255), nullable=False)
    thumbnail_file_path = Column(String(255), nullable=False)
    description = Column(TEXT, nullable=True)
    exif = Column(PickleType, nullable=False)
    metainfo = Column(PickleType, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    tags = relationship("Tag", secondary="image_tag", backref="images")

    def __repr__(self):
        return f"Image(id={self.id!r}, original_file_path={self.original_file_path!r}, thumbnail_file_path={self.thumbnail_file_path!r}, description={self.description!r}, exif={self.exif!r}, metainfo={self.metainfo!r}, created_at={self.created_at!r})"

class ImageTag(Base):
    __tablename__ = "image_tag"
    image_id = Column(Integer, ForeignKey("image.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tag.id"), primary_key=True)

class UserStore(Base):
    __tablename__ = "user_store"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    store_name = Column(TEXT, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    user = relationship("User", backref="user_store")

class UserImageStore(Base):
    __tablename__ = "user_image_store"
    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey("image.id"))
    store_id = Column(Integer, ForeignKey("user_store.id"))
    created_at = Column(DateTime, default=datetime.now())
    image = relationship("Image", backref="user_image_store")
    user_store = relationship("UserStore", backref="user_image_store")