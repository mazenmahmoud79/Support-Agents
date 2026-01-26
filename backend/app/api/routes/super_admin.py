"""
Super Admin routes for tenant management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import secrets
import os
from pathlib import Path
from typing import Optional, List
from app.db.session import get_db
from app.db.session import get_db
from app.models.database import Tenant, DemoUser
from app.core.logging import get_logger
from app.core.security import generate_api_key
from datetime import datetime

logger = get_logger(__name__)

router = APIRouter(prefix="/super-admin", tags=["Super Admin"])

DEMO_IDS_PATH = Path(__file__).parent.parent.parent.parent / "demo_ids.json"


# ============ Schemas ============

class AdminLoginRequest(BaseModel):
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    message: str


class TenantCreate(BaseModel):
    name: str


class TenantUpdate(BaseModel):
    is_active: Optional[bool] = None
    name: Optional[str] = None


class TenantInfo(BaseModel):
    id: int
    tenant_id: str
    name: str
    demo_id: str
    slug: Optional[str]
    is_active: bool
    created_at: datetime
    document_count: int = 0

    @property
    def is_active_bool(self) -> bool:
        return bool(self.is_active)

    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    tenants: List[TenantInfo]
    total: int


# ============ Helpers ============

def get_super_admin_password():
    """Get super admin password from environment."""
    password = os.getenv("SUPER_ADMIN_PASSWORD", "admin123")
    return password





def generate_demo_id():
    """Generate a unique demo ID like DEMO-XXXXXX."""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    suffix = ''.join(secrets.choice(chars) for _ in range(6))
    return f"DEMO-{suffix}"


def verify_admin_token(authorization: str = None):
    """Simple token verification - check header matches password."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    expected = f"Bearer {get_super_admin_password()}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return True


# ============ Routes ============

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """Verify super admin password."""
    if request.password == get_super_admin_password():
        return AdminLoginResponse(success=True, message="Login successful")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid password"
    )


@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants(
    db: Session = Depends(get_db)
):
    """List all tenants with their demo IDs."""
    # Get all tenants from database
    tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).all()
    
    result = []
    for tenant in tenants:
        # Find primary demo user (admin)
        demo_user = db.query(DemoUser).filter(
            DemoUser.tenant_id == tenant.tenant_id,
            DemoUser.is_active == 1
        ).order_by(DemoUser.created_at.asc()).first()
        
        demo_id = demo_user.demo_id if demo_user else "N/A"
        
        # Count documents for this tenant
        from app.models.database import Document
        doc_count = db.query(Document).filter(
            Document.tenant_id == tenant.tenant_id
        ).count()
        
        result.append(TenantInfo(
            id=tenant.id,
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            demo_id=demo_id,
            slug=tenant.slug,
            is_active=bool(tenant.is_active),
            created_at=tenant.created_at,
            document_count=doc_count
        ))
    
    return TenantListResponse(tenants=result, total=len(result))


@router.post("/tenants", response_model=TenantInfo)
async def create_tenant(
    request: TenantCreate,
    db: Session = Depends(get_db)
):
    """Create a new tenant with auto-generated demo ID."""
    # Generate unique demo ID
    demo_id = generate_demo_id()
    while db.query(DemoUser).filter(DemoUser.demo_id == demo_id).first():
        demo_id = generate_demo_id()
    
    # Generate tenant ID and slug
    name_slug = request.name.lower().replace(" ", "_").replace("-", "_")
    tenant_id = f"tenant_{name_slug}_{secrets.token_hex(3)}"
    slug = request.name.lower().replace(" ", "-").replace("_", "-")
    
    # Create tenant in database
    new_tenant = Tenant(
        tenant_id=tenant_id,
        name=request.name,
        slug=slug,
        api_key=generate_api_key(),
        is_active=1  # Use integer for database
    )
    
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    
    # Create Admin Demo User for this tenant
    demo_user = DemoUser(
        demo_id=demo_id,
        tenant_id=tenant_id,
        name=f"Admin for {request.name}",
        is_active=1,
        created_at=datetime.utcnow()
    )
    db.add(demo_user)
    db.commit()
    
    logger.info(f"Created tenant: {request.name} with demo ID: {demo_id}")
    
    return TenantInfo(
        id=new_tenant.id,
        tenant_id=new_tenant.tenant_id,
        name=new_tenant.name,
        demo_id=demo_id,
        slug=new_tenant.slug,
        is_active=bool(new_tenant.is_active),
        created_at=new_tenant.created_at,
        document_count=0
    )


@router.patch("/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    request: TenantUpdate,
    db: Session = Depends(get_db)
):
    """Update tenant (activate/deactivate)."""
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if request.is_active is not None:
        tenant.is_active = 1 if request.is_active else 0
    
    if request.name is not None:
        tenant.name = request.name
    
    db.commit()
    
    return {"success": True, "message": "Tenant updated"}


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Delete a tenant (soft delete - just deactivate and remove from demo IDs)."""
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Deactivate all demo users for this tenant
    db.query(DemoUser).filter(DemoUser.tenant_id == tenant_id).update({"is_active": 0})
    
    # Deactivate tenant (soft delete)
    tenant.is_active = 0
    db.commit()
    
    logger.info(f"Deleted tenant: {tenant.name}")
    
    return {"success": True, "message": "Tenant deleted"}


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get overview stats for super admin."""
    total_tenants = db.query(Tenant).count()
    active_tenants = db.query(Tenant).filter(Tenant.is_active == 1).count()
    
    from app.models.database import Document
    total_documents = db.query(Document).count()
    
    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "inactive_tenants": total_tenants - active_tenants,
        "total_documents": total_documents
    }
