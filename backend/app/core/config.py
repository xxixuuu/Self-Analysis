"""
Application configuration using Pydantic Settings.
All configuration is loaded from environment variables.
"""
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="LifeMetrics", description="Application name")
    app_env: str = Field(default="development", description="Environment")
    debug: bool = Field(default=True, description="Debug mode")
    secret_key: str = Field(..., description="Secret key for JWT")
    encryption_key: str = Field(..., description="Encryption key for sensitive data")

    # Server
    backend_host: str = Field(default="0.0.0.0", description="Backend host")
    backend_port: int = Field(default=8000, description="Backend port")

    # Database
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="lifemetrics", description="PostgreSQL database")
    postgres_user: str = Field(default="lifemetrics_user", description="PostgreSQL user")
    postgres_password: str = Field(..., description="PostgreSQL password")

    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Redis
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database")

    @property
    def redis_url(self) -> str:
        """Construct Redis URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # MinIO
    minio_host: str = Field(default="localhost", description="MinIO host")
    minio_port: int = Field(default=9000, description="MinIO port")
    minio_root_user: str = Field(default="minioadmin", description="MinIO root user")
    minio_root_password: str = Field(..., description="MinIO root password")
    minio_bucket: str = Field(default="lifemetrics-data", description="MinIO bucket")
    minio_secure: bool = Field(default=False, description="Use HTTPS for MinIO")

    @property
    def minio_endpoint(self) -> str:
        """Construct MinIO endpoint."""
        return f"{self.minio_host}:{self.minio_port}"

    # Ollama
    ollama_host: str = Field(default="localhost", description="Ollama host")
    ollama_port: int = Field(default=11434, description="Ollama port")
    ollama_model: str = Field(default="llama3.2", description="Default Ollama model")
    ollama_timeout: int = Field(default=120, description="Ollama timeout in seconds")

    @property
    def ollama_base_url(self) -> str:
        """Construct Ollama base URL."""
        return f"http://{self.ollama_host}:{self.ollama_port}"

    # Celery
    celery_broker_url: Optional[str] = Field(default=None, description="Celery broker URL")
    celery_result_backend: Optional[str] = Field(default=None, description="Celery result backend")
    celery_worker_concurrency: int = Field(default=4, description="Celery worker concurrency")

    @property
    def celery_broker(self) -> str:
        """Get Celery broker URL."""
        return self.celery_broker_url or self.redis_url

    @property
    def celery_backend(self) -> str:
        """Get Celery result backend URL."""
        return self.celery_result_backend or self.redis_url

    # OAuth2 - GitHub
    github_client_id: Optional[str] = Field(default=None, description="GitHub client ID")
    github_client_secret: Optional[str] = Field(default=None, description="GitHub client secret")
    github_redirect_uri: str = Field(
        default="http://localhost:3000/auth/github/callback",
        description="GitHub redirect URI"
    )

    # OAuth2 - Twitter
    twitter_client_id: Optional[str] = Field(default=None, description="Twitter client ID")
    twitter_client_secret: Optional[str] = Field(default=None, description="Twitter client secret")
    twitter_redirect_uri: str = Field(
        default="http://localhost:3000/auth/twitter/callback",
        description="Twitter redirect URI"
    )

    # OAuth2 - Google
    google_client_id: Optional[str] = Field(default=None, description="Google client ID")
    google_client_secret: Optional[str] = Field(default=None, description="Google client secret")
    google_redirect_uri: str = Field(
        default="http://localhost:3000/auth/google/callback",
        description="Google redirect URI"
    )

    # OAuth2 - Slack
    slack_client_id: Optional[str] = Field(default=None, description="Slack client ID")
    slack_client_secret: Optional[str] = Field(default=None, description="Slack client secret")
    slack_redirect_uri: str = Field(
        default="http://localhost:3000/auth/slack/callback",
        description="Slack redirect URI"
    )

    # OAuth2 - Spotify
    spotify_client_id: Optional[str] = Field(default=None, description="Spotify client ID")
    spotify_client_secret: Optional[str] = Field(default=None, description="Spotify client secret")
    spotify_redirect_uri: str = Field(
        default="http://localhost:3000/auth/spotify/callback",
        description="Spotify redirect URI"
    )

    # Data Collection
    collection_interval_minutes: int = Field(
        default=60,
        description="Data collection interval in minutes"
    )
    data_retention_days: int = Field(
        default=365,
        description="Data retention period in days"
    )
    enable_auto_collection: bool = Field(
        default=True,
        description="Enable automatic data collection"
    )

    # Security
    jwt_secret_key: str = Field(..., description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(
        default=60,
        description="JWT expiration time in minutes"
    )
    enable_encryption: bool = Field(default=True, description="Enable data encryption")
    enable_audit_log: bool = Field(default=True, description="Enable audit logging")

    # Privacy
    gdpr_mode: bool = Field(default=True, description="GDPR compliance mode")
    allow_data_export: bool = Field(default=True, description="Allow data export")
    allow_data_deletion: bool = Field(default=True, description="Allow data deletion")
    anonymize_old_data: bool = Field(default=False, description="Anonymize old data")

    # Monitoring
    log_level: str = Field(default="INFO", description="Log level")
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_profiling: bool = Field(default=False, description="Enable profiling")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins"
    )
    cors_credentials: bool = Field(default=True, description="CORS allow credentials")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(
        default=60,
        description="Rate limit per minute"
    )


# Create global settings instance
settings = Settings()
