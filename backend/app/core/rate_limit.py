"""
DSRA V2 — Rate Limiting Configuration
======================================
Sets up slowapi rate limiter instance using key_func mappings.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import get_settings

settings = get_settings()


def get_user_identifier(request: Request) -> str:
    """
    Generate rate limiting keys. Prefer authenticated user email/ID,
    falling back to client IP address.
    """
    # Check if request state has current_user (if loaded by dependencies/middleware)
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "email"):
        return f"user:{user.email}"
    
    # Fallback to standard remote address (IP)
    return get_remote_address(request)


# Initialize slowapi limiter
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=[settings.rate_limit_default]
)
