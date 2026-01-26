"""
Authentication routes for tenant registration and login.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import Tenant, Analytics, DemoUser
from app.models.schemas import TenantResponse, DemoLogin
from app.services.vector_store import get_vector_store
from app.core.logging import get_logger
from datetime import datetime

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TenantResponse)
async def demo_login(
    login_data: DemoLogin,
    db: Session = Depends(get_db)
):
    """
    Login using a demo access ID from pre-configured list.
    
    Validates against demo_ids.json file.
    """
    # Query DemoUser directly
    demo_user = db.query(DemoUser).filter(
        DemoUser.demo_id == login_data.demo_id,
        DemoUser.is_active == 1
    ).first()
    
    if not demo_user:
        logger.warning(f"Demo login failed: invalid demo ID {login_data.demo_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid demo ID"
        )
    
    # Check expiration
    if demo_user.expires_at and demo_user.expires_at < datetime.utcnow():
        logger.warning(f"Demo key expired: {login_data.demo_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Demo key expired"
        )
        
    # Get associated tenant
    tenant = db.query(Tenant).filter(Tenant.tenant_id == demo_user.tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
        
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is inactive"
        )
        
    # Update usage stats
    demo_user.usage_count += 1
    demo_user.last_used_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Login successful: {login_data.demo_id} (Tenant: {tenant.name})")
    
    return TenantResponse(
        id=tenant.id,
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        api_key=tenant.api_key,
        created_at=tenant.created_at,
        is_active=bool(tenant.is_active)
    )

