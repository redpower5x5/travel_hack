from app.core import crud
from app.config import settings
from app.core.dependencies import pwd_context, oauth2_scheme, get_db, alternate_oauth2_scheme
from app.schemas.response_schemas import TokenData, User
from app.config import log

from jose import jwt, JWTError
from typing import Optional, Annotated
from fastapi import HTTPException, status, Depends
from datetime import datetime, timedelta
from sqlalchemy.orm import Session


def verify_password(plain_password, hashed_password):
    log.info(f"Verifying password {plain_password} against {hashed_password}")
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str):
    user = crud.get_user(db, email)
    if user is None:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

no_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_user(
        token: Annotated[str, Depends(alternate_oauth2_scheme)],
        db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None or token == "":
        return None
    log.info(f'Getting current user from token {token}')
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        log.info(f'{payload}')
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = crud.get_user(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    user = User(
        id=user.id,
        username=user.username,
        email=user.email,
    )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user is None:
        raise no_token_exception
    return current_user

async def get_current_soft_client(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user

async def get_current_active_admin(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user is None:
        raise no_token_exception
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user