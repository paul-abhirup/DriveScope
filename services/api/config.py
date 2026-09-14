import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "DriveScope"
    MODE: str = "minimal"  # "minimal" (in-process + sqlite) or "docker" (celery + postgres)
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "drivescope-dev-insecure-secret-key"

    DATABASE_URL: str = "sqlite:///./drivescope.db"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    STORAGE_PROVIDER: str = "local"
    STORAGE_LOCAL_DIR: str = "./data"
    OBJECT_STORE_ENDPOINT: Optional[str] = None
    OBJECT_STORE_BUCKET: str = "drivescope-artifacts"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
