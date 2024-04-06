from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from typing import Annotated
from datetime import timedelta

from app.config import log
from app.schemas import response_schemas, request_schemas
from app.core.dependencies import get_db
from app.core import crud
from app.config import settings
from app.utils.token import get_current_active_user
from app.utils.token import (
    authenticate_user,
    create_access_token,
)
from app.utils.email import verify_email

router = APIRouter(
    prefix="/user",
    tags=["user"],
)


@router.post("/create", response_model=response_schemas.Token)
async def create_user(
    user: request_schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user
    """
    db_user = crud.get_user(db, user.email)

    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # is_valid_email = verify_email(user.email)

    # if not is_valid_email:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email is not valid",
    #     )

    user = crud.create_user(db=db, user=user)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=response_schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    we use username in OAuth2PasswordRequestForm as email
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/profile", response_model=response_schemas.User)
async def get_user_profile(
    current_user: response_schemas.User = Depends(get_current_active_user),
):
    return current_user

@router.put("/update", response_model=response_schemas.User)
async def update_user(
    user: request_schemas.UserUpdate,
    current_user: response_schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Update user profile
    """
    return crud.user_update(db=db, user=user, current_user=current_user)