"""EFL Agent Assistant - Main FastAPI Application"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from src.api import health, track, containers, bl, sessions, session_messages, voice
from src.core.config import settings
from src.lib.circuit_breaker import CircuitBreakerManager
from src.lib.logger import setup_logger
from src.middleware.auth import AuthMiddleware
from src.middleware.error_handler import ErrorHandlerMiddleware
from src.middleware.localisation import LocalisationMiddleware
from src.middleware.logging import LoggingMiddleware
from src.middleware.security import SecurityMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print(f"🚀 Starting EFL Agent Assistant v{settings.VERSION}")
    print(f"📍 Environment: {settings.ENVIRONMENT}")

    # Initialize logging
    setup_logger(
        name="efl_agent",
        level=settings.LOG_LEVEL,
        log_file="logs/app.log" if settings.ENVIRONMENT != "testing" else None
    )

    # Initialize circuit breaker manager
    CircuitBreakerManager.initialize()

    yield

    # Shutdown
    print("🛑 Shutting down EFL Agent Assistant")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="EFL Agent Assistant for Container Tracking with Voice and Chat Support",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Rate limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging middleware (should be early in the chain)
    if settings.ENABLE_REQUEST_LOGGING:
        app.add_middleware(LoggingMiddleware, log_level=settings.LOG_LEVEL)

    # Localisation middleware (enables cultural context + language detection)
    if settings.ENABLE_LOCALISATION:
        app.add_middleware(
            LocalisationMiddleware,
            default_language=settings.DEFAULT_LANGUAGE,
            default_cultural_context=settings.DEFAULT_CULTURAL_CONTEXT,
            supported_languages=settings.SUPPORTED_LANGUAGES,
            supported_cultural_contexts=settings.SUPPORTED_CULTURAL_CONTEXTS,
        )

    # Authentication middleware (runs before localisation due to middleware stacking order)
    app.add_middleware(AuthMiddleware)

    # Security middleware (temporarily disabled for debugging)
    # app.add_middleware(SecurityMiddleware)

    # Error handler middleware captures exceptions and returns cultural responses
    app.add_middleware(ErrorHandlerMiddleware)

    # Rate limiting middleware (temporarily disabled for debugging)
    # app.add_middleware(SlowAPIMiddleware)

    # Include routers
    app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
    app.include_router(track.router, prefix=settings.API_V1_STR, tags=["tracking"])
    app.include_router(containers.router, prefix=settings.API_V1_STR, tags=["containers"])
    app.include_router(bl.router, prefix=settings.API_V1_STR, tags=["bill-of-lading"])
    app.include_router(sessions.router, prefix=settings.API_V1_STR, tags=["sessions"])
    app.include_router(session_messages.router, prefix=settings.API_V1_STR, tags=["session-messages"])

    # Voice router (only include if voice is enabled)
    if settings.ENABLE_VOICE:
        app.include_router(voice.router, prefix=settings.API_V1_STR, tags=["voice"])

    return app


app = create_application()


@app.get("/")
async def root():
    """Root endpoint with basic service information."""
    return {
        "service": "EFL Agent Assistant",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational"
    }


@app.get("/test")
async def test():
    """Simple test endpoint."""
    return {"message": "test endpoint working"}
