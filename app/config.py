"""Configuración del proyecto desde variables de entorno."""

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración centralizada desde .env."""

    # OpenRouter / LLM
    openrouter_api_key: str
    openrouter_model: str = "google/gemini-2.0-flash-001"

    # Auth (JWT)
    app_username: str
    app_password: str
    jwt_secret_key: str
    jwt_expire_minutes: int = 480

    # Database
    database_url: str

    # App
    max_file_size_mb: int = 10
    environment: str = "development"

    @field_validator("database_url")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """Auto-corrige DATABASE_URL para usar asyncpg."""
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
