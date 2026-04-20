"""
API dependencies for authentication and database access.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Tenant, User
from app.core.security import verify_token
from app.core.logging import get_logger

logger = get_logger(__name__)

_http_bearer = HTTPBearer(auto_error=False)


async def get_current_tenant(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_http_bearer),
    db: Session = Depends(get_db),
) -> Tenant:
    """
    Dependency that validates the Bearer JWT and returns the active Tenant.
    Performs a DB lookup on every request to ensure user/tenant are still valid.
    """
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header required")

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not found or unverified")

    tenant = db.query(Tenant).filter(
        Tenant.tenant_id == tenant_id,
        Tenant.is_active == 1,
    ).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization not found or inactive")

    logger.debug(f"Authenticated: {user.email} → {tenant.tenant_id}")
    return tenant


async def get_optional_tenant(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_http_bearer),
    db: Session = Depends(get_db),
) -> Optional[Tenant]:
    """Same as get_current_tenant but returns None instead of raising on missing/invalid auth."""
    if not credentials:
        return None
    try:
        payload = verify_token(credentials.credentials)
        if not payload:
            return None
        tenant_id = payload.get("tenant_id")
        tenant = db.query(Tenant).filter(
            Tenant.tenant_id == tenant_id,
            Tenant.is_active == 1,
        ).first()
        return tenant
    except Exception:
        return None

