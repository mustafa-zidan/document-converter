"""Application configuration."""

from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Attributes:
        API_V1_STR: API version 1 prefix.
        API_V2_STR: API version 2 prefix.
        PROJECT_NAME: Name of the project.
        BACKEND_CORS_ORIGINS: List of allowed CORS origins.
        DEBUG: Debug mode.
        MAX_UPLOAD_SIZE: Maximum upload size in bytes (default: 10MB).
        ALLOWED_EXTENSIONS: List of allowed file extensions.
        OCR_ENABLED: Whether to enable OCR for scanned PDFs.
        SMOLDOCLING_MODEL: Model name for SmolDocling service.
    """

    API_V1_STR: str = "/api/v1"
    API_V2_STR: str = "/api/v2"
    PROJECT_NAME: str = "Document Converter API"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    DEBUG: bool = False
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf"]
    OCR_ENABLED: bool = True
    SMOLDOCLING_MODEL: str = "ds4sd/SmolDocling-256M-preview"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Validate CORS origins.

        Args:
            v: CORS origins as string or list.

        Returns:
            Validated CORS origins.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
