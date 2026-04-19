"""
Super Admin routes for tenant management.
All routes require admin JWT authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import hmac
import secrets
from pathlib import Path
from typing import Optional, List
from app.db.session import get_db
from app.models.database import Tenant, DemoUser
from app.core.logging import get_logger
from app.core.security import generate_api_key, create_access_token, verify_token
from app.core.rate_limit import limiter, AUTH_LIMIT, ADMIN_LIMIT
from app.config import settings
from datetime import datetime, timedelta

logger = get_logger(__name__)

router = APIRouter(prefix="/super-admin", tags=["Super Admin"])

DEMO_IDS_PATH = Path(__file__).parent.parent.parent.parent / "demo_ids.json"


# ============ Schemas ============

class AdminLoginRequest(BaseModel):
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None


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


# ============ Auth Dependency ============

def generate_demo_id():
    """Generate a unique demo ID like DEMO-XXXXXX."""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    suffix = ''.join(secrets.choice(chars) for _ in range(6))
    return f"DEMO-{suffix}"


async def require_admin(authorization: str = Header(...)):
    """
    Dependency: validate admin JWT from Authorization header.
    Issues JWT on login; all other routes require it.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    payload = verify_token(token)
    if not payload or payload.get("role") != "super_admin":
        raise HTTPException(status_code=401, detail="Invalid or expired admin token")
    return payload


# ============ Routes ============

@router.post("/login", response_model=AdminLoginResponse)
@limiter.limit(AUTH_LIMIT)
async def admin_login(request: Request, body: AdminLoginRequest):
    """Verify super admin password and return a JWT."""
    expected = settings.SUPER_ADMIN_PASSWORD
    if not expected:
        raise HTTPException(status_code=503, detail="Admin login not configured")

    if not hmac.compare_digest(body.password, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )

    token = create_access_token(
        data={"sub": "super_admin", "role": "super_admin"},
        expires_delta=timedelta(hours=8),
    )
    return AdminLoginResponse(success=True, message="Login successful", token=token)


@router.get("/tenants", response_model=TenantListResponse)
@limiter.limit(ADMIN_LIMIT)
async def list_tenants(
    request: Request,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all tenants with their demo IDs."""
    tenants = db.query(Tenant).order_by(Tenant.created_at.desc()).all()

    result = []
    for tenant in tenants:
        demo_user = db.query(DemoUser).filter(
            DemoUser.tenant_id == tenant.tenant_id,
            DemoUser.is_active == 1
        ).order_by(DemoUser.created_at.asc()).first()

        demo_id = demo_user.demo_id if demo_user else "N/A"

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
            document_count=doc_count,
        ))

    return TenantListResponse(tenants=result, total=len(result))


@router.post("/tenants", response_model=TenantInfo)
@limiter.limit(ADMIN_LIMIT)
async def create_tenant(
    request: Request,
    body: TenantCreate,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new tenant with auto-generated demo ID."""
    demo_id = generate_demo_id()
    while db.query(DemoUser).filter(DemoUser.demo_id == demo_id).first():
        demo_id = generate_demo_id()

    name_slug = body.name.lower().replace(" ", "_").replace("-", "_")
    tenant_id = f"tenant_{name_slug}_{secrets.token_hex(3)}"
    slug = body.name.lower().replace(" ", "-").replace("_", "-")

    new_tenant = Tenant(
        tenant_id=tenant_id,
        name=body.name,
        slug=slug,
        api_key=generate_api_key(),
        is_active=1,
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    demo_user = DemoUser(
        demo_id=demo_id,
        tenant_id=tenant_id,
        name=f"Admin for {body.name}",
        is_active=1,
        created_at=datetime.utcnow(),
    )
    db.add(demo_user)
    db.commit()

    logger.info(f"Created tenant: {body.name} (id={tenant_id})")

    return TenantInfo(
        id=new_tenant.id,
        tenant_id=new_tenant.tenant_id,
        name=new_tenant.name,
        demo_id=demo_id,
        slug=new_tenant.slug,
        is_active=bool(new_tenant.is_active),
        created_at=new_tenant.created_at,
        document_count=0,
    )


@router.patch("/tenants/{tenant_id}")
@limiter.limit(ADMIN_LIMIT)
async def update_tenant(
    tenant_id: str,
    body: TenantUpdate,
    request: Request,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update tenant (activate/deactivate)."""
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if body.is_active is not None:
        tenant.is_active = 1 if body.is_active else 0
    if body.name is not None:
        tenant.name = body.name

    db.commit()
    return {"success": True, "message": "Tenant updated"}


@router.delete("/tenants/{tenant_id}")
@limiter.limit(ADMIN_LIMIT)
async def delete_tenant(
    tenant_id: str,
    request: Request,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Soft-delete a tenant."""
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    db.query(DemoUser).filter(DemoUser.tenant_id == tenant_id).update({"is_active": 0})
    tenant.is_active = 0
    db.commit()

    logger.info(f"Deleted tenant: {tenant.name}")
    return {"success": True, "message": "Tenant deleted"}


@router.get("/stats")
@limiter.limit(ADMIN_LIMIT)
async def get_stats(
    request: Request,
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get overview stats for super admin."""
    total_tenants = db.query(Tenant).count()
    active_tenants = db.query(Tenant).filter(Tenant.is_active == 1).count()

    from app.models.database import Document
    total_documents = db.query(Document).count()

    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "inactive_tenants": total_tenants - active_tenants,
        "total_documents": total_documents,
    }
