"""Application configuration settings."""
from typing import Any, List
from pydantic import PostgresDsn, RedisDsn, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "HyperToQ Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    API_V1_PREFIX: str = "/api/v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False

    # Database
    DATABASE_URL: PostgresDsn
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 0

    # Redis
    REDIS_URL: RedisDsn
    REDIS_CACHE_TTL: int = 3600

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate SECRET_KEY is set and strong enough."""
        if not v:
            raise ValueError("SECRET_KEY must be set")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if v in ["your-super-secret-key-change-this-in-production", "changeme", "secret"]:
            raise ValueError("SECRET_KEY must not be a default/common value")
        return v

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_token_expiry(cls, v: int) -> int:
        """Validate token expiry time is reasonable."""
        if v < 5:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be at least 5 minutes")
        if v > 1440:  # 24 hours
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES should not exceed 24 hours")
        return v

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Google Generative AI
    GOOGLE_API_KEY: str
    GEMINI_MODEL: str = "gemini-pro"

    @field_validator("GOOGLE_API_KEY")
    @classmethod
    def validate_google_api_key(cls, v: str, info: ValidationInfo) -> str:
        """Validate Google API key is set in production."""
        environment = info.data.get("ENVIRONMENT", "production")
        if environment == "production" and not v:
            raise ValueError("GOOGLE_API_KEY must be set in production")
        if v and v == "your-google-api-key-here":
            raise ValueError("GOOGLE_API_KEY must not be the default value")
        return v

    # LemonSqueezy
    LEMONSQUEEZY_API_KEY: str
    LEMONSQUEEZY_STORE_ID: str
    LEMONSQUEEZY_WEBHOOK_SECRET: str

    @field_validator("LEMONSQUEEZY_API_KEY")
    @classmethod
    def validate_lemonsqueezy_key(cls, v: str, info: ValidationInfo) -> str:
        """Validate LemonSqueezy API key is set in production."""
        environment = info.data.get("ENVIRONMENT", "production")
        if environment == "production" and not v:
            raise ValueError("LEMONSQUEEZY_API_KEY must be set in production")
        if v and v == "your-lemonsqueezy-api-key":
            raise ValueError("LEMONSQUEEZY_API_KEY must not be the default value")
        return v

    # Email (Optional)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values."""
        allowed = ["development", "staging", "production", "testing"]
        if v.lower() not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of: {', '.join(allowed)}")
        return v.lower()

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return str(self.DATABASE_URL).replace("+asyncpg", "")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    @classmethod
    def generate_secret_key(cls) -> str:
        """Generate a secure random secret key."""
        return secrets.token_urlsafe(32)


# Global settings instance
settings = Settings()
