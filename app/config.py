"""Application settings loaded from environment variables / .env file."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# app/config.py (изменения)

class Settings(BaseSettings):
    """Centralized application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Budget Manager API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = Field(
        default="postgresql://budget:budget@localhost:5432/budget",  # Убрал +asyncpg
        description="PostgreSQL DSN (asyncpg will be added automatically)",
    )
    
    @property
    def async_database_url(self) -> str:
        """Returns database URL with asyncpg driver for SQLAlchemy."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Добавляем SSL для Render PostgreSQL
        if "?" not in url:
            url += "?ssl=require"
        elif "ssl=" not in url:
            url += "&ssl=require"
        
        return url

    # JWT
    jwt_secret: str = Field(default="change-me", min_length=8)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # CORS - добавим Render домен по умолчанию
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500"

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        # Добавляем GitHub Pages домен, если он есть в переменных
        if self.github_pages_url:
            origins.append(self.github_pages_url)
        return origins
    
    # Дополнительные настройки для Render
    github_pages_url: str = Field(default="", description="Frontend URL for CORS")


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (one instance per process)."""
    return Settings()


settings = get_settings()
