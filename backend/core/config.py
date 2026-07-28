"""
DevVerse AI - Core Configuration

Centralized configuration management using Pydantic Settings.
Supports environment-based configuration with validation.
"""

from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "DevVerse AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    API_V2_PREFIX: str = "/api/v2"
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://devverse:devverse_secret@localhost:5432/devverse",
        description="PostgreSQL connection URL"
    )
    DB_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow")
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    REDIS_DB: int = Field(default=0, description="Redis database number")
    
    # Qdrant
    QDRANT_URL: str = Field(
        default="http://localhost:6333",
        description="Qdrant vector database URL"
    )
    QDRANT_API_KEY: Optional[str] = Field(default=None, description="Qdrant API key")
    
    # Security
    SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT and encryption"
    )
    ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = Field(default=30, description="JWT token expiry in minutes")
    REFRESH_TOKEN_EXPIRY_DAYS: int = Field(
        default=7,
        description="Refresh token expiry in days"
    )
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: Optional[str] = Field(default=None, description="GitHub OAuth client ID")
    GITHUB_CLIENT_SECRET: Optional[str] = Field(
        default=None,
        description="GitHub OAuth client secret"
    )
    GITHUB_REDIRECT_URI: str = Field(
        default="http://localhost:8000/api/v1/auth/github/callback",
        description="GitHub OAuth redirect URI"
    )
    GITHUB_TOKEN: Optional[str] = Field(default=None, description="GitHub personal access token")
    
    # Celery
    CELERY_BROKER_URL: Optional[str] = Field(
        default=None,
        description="Celery broker URL (defaults to Redis)"
    )
    CELERY_RESULT_BACKEND: Optional[str] = Field(
        default=None,
        description="Celery result backend"
    )
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Default rate limit per minute"
    )
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    
    # AI/LLM
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    LLM_MODEL: str = Field(default="gpt-4-turbo-preview", description="Default LLM model")
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="Embedding model for vectors"
    )
    MAX_TOKENS: int = Field(default=4096, description="Max tokens for LLM responses")
    
    # Vector Search
    VECTOR_DIMENSION: int = Field(
        default=1536,
        description="Vector dimension for embeddings"
    )
    VECTOR_COLLECTION_NAME: str = Field(
        default="devverse_embeddings",
        description="Qdrant collection name"
    )
    
    # File Storage
    UPLOAD_DIR: str = Field(default="/tmp/uploads", description="Upload directory")
    MAX_UPLOAD_SIZE: int = Field(
        default=10 * 1024 * 1024,
        description="Max upload size in bytes"
    )
    
    # Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = Field(
        default=None,
        description="OpenTelemetry exporter endpoint"
    )
    PROMETHEUS_ENABLED: bool = Field(default=True, description="Enable Prometheus metrics")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT.lower() == "testing"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures we only load settings once,
    improving performance across the application.
    """
    return Settings()


# Global settings instance
settings = get_settings()
