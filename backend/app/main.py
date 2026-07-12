"""
DSRA V2 — FastAPI Application Entry Point
==========================================
Initializes the web framework, registers endpoints, configures CORS,
attaches rate limiters, and binds global exception handlers.
"""

import structlog
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.research import router as research_router
from app.config.settings import get_settings

settings = get_settings()
from app.core.logging import get_logger
from app.core.rate_limit import limiter
from app.db.session import check_db_health

log = get_logger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title="DSRA V2 API",
    description="Deep Scientific Research Architect Platform API Services",
    version="2.0.0"
)

# Attach slowapi rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler := lambda r, e: limiter._rate_limit_exceeded_handler(r, e))

# CORS configuration
# Allows connection from local development server (Vite default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(research_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event() -> None:
    """Verify system health on startup."""
    log.info("application_startup_initiated")
    db_healthy = await check_db_health()
    if db_healthy:
        log.info("database_health_check_passed")
    else:
        log.warning("database_health_check_failed_on_startup")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup resources on shutdown."""
    log.info("application_shutdown_completed")


@app.get("/health", status_code=status.HTTP_200_OK, tags=["System Integrity"])
async def health_check() -> dict[str, str]:
    """Simple API status checks returning JSON."""
    db_healthy = await check_db_health()
    return {
        "status": "online",
        "database": "connected" if db_healthy else "disconnected",
        "environment": settings.app_env
    }
