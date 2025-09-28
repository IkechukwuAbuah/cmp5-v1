"""Application configuration settings."""

import secrets
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Project
    PROJECT_NAME: str = "EFL Agent Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @model_validator(mode="after")
    def assemble_cors_origins(self) -> "Settings":
        if isinstance(self.BACKEND_CORS_ORIGINS, str) and not self.BACKEND_CORS_ORIGINS:
            return self
        elif isinstance(self.BACKEND_CORS_ORIGINS, list):
            return self

        cors_origins = []
        for origin in self.BACKEND_CORS_ORIGINS:
            if isinstance(origin, str):
                cors_origins.append(AnyHttpUrl(origin))
        self.BACKEND_CORS_ORIGINS = cors_origins
        return self

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"

    # Database/Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SESSION_TTL: int = 3600  # 1 hour
    REDIS_MAX_CONNECTIONS: int = 20

    # External APIs
    EFL_TERMINAL_API_URL: str = "https://api.eflterminal.com"
    EFL_TERMINAL_API_KEY: str = ""
    CMA_CGM_API_URL: str = "https://api.cma-cgm.com"
    CMA_CGM_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60  # requests per minute per IP
    RATE_LIMIT_BURST: int = 10

    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60  # seconds
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: str = "Exception"

    # Performance
    MAX_RESPONSE_TIME_MS: int = 5000  # 5 seconds
    MAX_VOICE_RESPONSE_TIME_MS: int = 20000  # 20 seconds
    MAX_CONCURRENT_USERS: int = 100
    MAX_CONTAINERS_PER_DAY: int = 10000
    LOCALISATION_LATENCY_TARGET_MS: int = 50
    LOCALISATION_ACCURACY_THRESHOLD: float = 0.9

    # Session Management
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_SESSION_MESSAGES: int = 50
    SESSION_CLEANUP_INTERVAL: int = 300  # 5 minutes

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_RESPONSE_LOGGING: bool = True

    # Feature Flags
    ENABLE_VOICE: bool = True
    ENABLE_CHAT: bool = True
    ENABLE_LOCALISATION: bool = True
    DEFAULT_LANGUAGE: str = "en"
    DEFAULT_CULTURAL_CONTEXT: str = "nigerian"
    SUPPORTED_LANGUAGES: List[str] = ["en", "fr", "pt", "ar"]
    SUPPORTED_CULTURAL_CONTEXTS: List[str] = [
        "nigerian",
        "west_african",
        "formal_business",
    ]
    ENABLE_CIRCUIT_BREAKER: bool = True
    ENABLE_RATE_LIMITING: bool = True

    # Graceful Degradation
    ENABLE_FALLBACK_TO_CACHE: bool = True
    CACHE_STALENESS_TOLERANCE_MINUTES: int = 60

    # Development
    DEBUG: bool = False

    @computed_field
    @property
    def server_host(self) -> str:
        if self.ENVIRONMENT == "production":
            return "0.0.0.0"
        return "127.0.0.1"

    @computed_field
    @property
    def server_port(self) -> int:
        return 8000


settings = Settings()
