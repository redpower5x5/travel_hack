from loguru import logger
from typing import Any, Dict, List, Optional, Union
from pydantic import PostgresDsn, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

logger.add("debug.log", format="{time} {level} {message}", level="DEBUG")
log = logger


load_dotenv()


class Settings(BaseSettings):
    DOCKER_MODE: bool = True
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    LOGGING_LEVEL: str = "DEBUG"
    SERVICE_NAME: str

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    POSTGRES_HOST: str = "db"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_PORT: str
    POSTGRES_DB: str
    DATABASE_URI: Optional[PostgresDsn] = None
    MESSAGE_STREAM_DELAY: int = 1  # second
    MESSAGE_STREAM_RETRY_TIMEOUT: int = 15000  # milisecond

    REDIS_URI: str = "redis://redis:6379"
    CACHE_EXPIRE: int = 30
    UPLOAD_FOLDER: str = "app/uploads"

    RESOURCE_ENDPOINT: str = "http://localhost:9000"
    ACCESS_SECRET: str
    ACCESS_KEY: str
    REGION: str
    DEFAULT_BUCKET: str

    IMGPROXY_HOST: str = "http://localhost:50200"

    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v

        return (
            f'postgresql+psycopg2://{values["POSTGRES_USER"]}:{values["POSTGRES_PASSWORD"]}@'
            f'{values["POSTGRES_HOST"]}:{values["POSTGRES_PORT"]}/{values["POSTGRES_DB"]}'
        )

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080 #10080
    ALLOWED_FILE_TYPES: List[str] = ["image/jpeg", "image/png", "image/jpg", "image/gif", "image/webp"]

    class Config:
        case_sensitive = True
        env_file_encoding = "utf-8"
        env_file = ".env"


settings = Settings()  # type: ignore
