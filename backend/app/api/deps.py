"""
API dependencies for authentication and database access.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Tenant
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_current_tenant(
    x_api_key: str = Header(..., description="API key for authentication"),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Dependency to get current authenticated tenant.
    
    Args:
        x_api_key: API key from header
        db: Database session
    
    Returns:
        Tenant: Authenticated tenant
    
    Raises:
        HTTPException: If authentication fails
    """
    # Query tenant by API key
    tenant = db.query(Tenant).filter(Tenant.api_key == x_api_key).first()
    
    if not tenant:
        logger.warning(f"Authentication failed for API key: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    if not tenant.is_active:
        logger.warning(f"Inactive tenant attempted access: {tenant.tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is inactive"
        )
    
    logger.debug(f"Authenticated tenant: {tenant.tenant_id}")
    return tenant


async def get_optional_tenant(
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[Tenant]:
    """
    Dependency to get current tenant (optional).
    
    Args:
        x_api_key: API key from header (optional)
        db: Database session
    
    Returns:
        Optional[Tenant]: Authenticated tenant or None
    """
    if not x_api_key:
        return None
    
    tenant = db.query(Tenant).filter(Tenant.api_key == x_api_key).first()
    return tenant if tenant and tenant.is_active else None
