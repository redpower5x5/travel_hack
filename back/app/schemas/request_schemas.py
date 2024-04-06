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
    phone: str


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
    phone: Optional[str]

