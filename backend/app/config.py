"""Application configuration using Pydantic Settings."""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Backend application settings."""

    # Server Settings
    APP_NAME: str = "AI Logo Color Extractor API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Settings
    ALLOWED_ORIGINS: str = "http://localhost:4200,http://127.0.0.1:4200,http://localhost:3000,http://127.0.0.1:3000,*"

    # OpenAI Settings
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")

    # Image Processing & Color Extraction
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "png,jpg,jpeg,webp"
    MAX_CLUSTERS: int = 16
    MIN_CLUSTERS: int = 8
    ALPHA_TRANSPARENCY_THRESHOLD: int = 30  # Alpha values below this are discarded as transparent
    IMAGE_RESIZE_MAX_DIM: int = 400  # Max dimension for clustering performance

    @property
    def allowed_origins_list(self) -> List[str]:
        """Return list of allowed CORS origins."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Return list of allowed file extensions."""
        return [ext.strip().lower().lstrip(".") for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
