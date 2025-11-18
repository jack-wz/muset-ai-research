"""Application configuration."""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Muset AI Writing Assistant"
    app_version: str = "0.1.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 7989

    # Database
    database_url: str = "postgresql://muset:muset@localhost:5432/muset"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 10

    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:7989"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # AI Models
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    default_model: str = "claude-3-5-sonnet-20241022"

    # File Storage
    upload_dir: str = "./uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB

    # Vector Database
    pinecone_api_key: Optional[str] = None
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "muset-memories"

    # MCP Configuration
    mcp_config_path: str = "./mcp_config.json"

    # Skills Configuration
    skills_dir: str = "./skills"

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    log_file: Optional[str] = None

    # Monitoring Configuration
    enable_metrics: bool = True
    metrics_port: int = 9090

    # Performance Configuration
    request_timeout: int = 30
    max_concurrent_requests: int = 100
    rate_limit_requests_per_minute: int = 60

    # Error Recovery Configuration
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60

    # Retry Configuration
    max_retries: int = 3
    retry_initial_delay: float = 1.0
    retry_max_delay: float = 60.0


settings = Settings()
