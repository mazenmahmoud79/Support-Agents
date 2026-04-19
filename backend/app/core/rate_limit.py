"""
Rate limiting configuration using slowapi.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri=settings.REDIS_URL if settings.REDIS_URL else "memory://",
)

# Rate limit constants for specific endpoint groups
AUTH_LIMIT = "5/minute"
CHAT_LIMIT = "30/minute"
UPLOAD_LIMIT = "10/minute"
PUBLIC_CHAT_LIMIT = "20/minute"
ADMIN_LIMIT = "60/minute"
