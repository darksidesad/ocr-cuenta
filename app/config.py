"""Configuración del proyecto desde variables de entorno."""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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
        """Auto-corrige DATABASE_URL para asyncpg."""
        # 1. Normalizar prefijo del dialecto
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]

        # 2. Parsear y limpiar parámetros que asyncpg no soporta
        parsed = urlparse(v)
        params = parse_qs(parsed.query)

        # Parámetros soportados por asyncpg
        supported = {"ssl", "sslcert", "sslkey", "sslrootcert", "application_name", "server_settings"}
        clean_params = {k: v_list[0] for k, v_list in params.items() if k in supported}

        clean_query = urlencode(clean_params) if clean_params else ""
        v = urlunparse(parsed._replace(query=clean_query))

        return v

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
