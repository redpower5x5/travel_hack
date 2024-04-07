from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict
from decimal import Decimal


class UserInDB(BaseModel):
    """
    User in database schema
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    hashed_password: str