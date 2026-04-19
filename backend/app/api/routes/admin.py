"""
Admin routes for dashboard, analytics, and system health.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.db.session import get_db
from app.api.deps import get_current_tenant
from app.models.database import Tenant, Document, ChatHistory, Analytics, DemoUser, TenantContext, EscalationLog
from app.models.schemas import AnalyticsResponse, HealthCheck, DemoUserCreate, DemoUserResponse, TenantContextUpdate, TenantContextResponse, EscalationLogResponse
from app.models.enums import Industry, ToneOfVoice, LanguageStyle, ResponseLength
from app.services.vector_store import get_vector_store
from app.services.llm_service import get_llm_service
from app.config import settings
from app.core.logging import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==================== Tenant Context Management ====================

@router.get("/context", response_model=TenantContextResponse)
async def get_tenant_context(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get the current tenant's context/profile settings.
    Creates default settings if none exist.
    """
    context = db.query(TenantContext).filter(
        TenantContext.tenant_id == tenant.tenant_id
    ).first()
    
    # Create default context if none exists
    if not context:
        context = TenantContext(
            tenant_id=tenant.tenant_id,
            company_name=tenant.name,
            industry=Industry.OTHER,
            tone_of_voice=ToneOfVoice.PROFESSIONAL,
            language_style=LanguageStyle.CONVERSATIONAL,
            response_length=ResponseLength.BALANCED
        )
        db.add(context)
        db.commit()
        db.refresh(context)
        logger.info(f"Created default context for tenant {tenant.tenant_id}")
    
    return context


@router.put("/context", response_model=TenantContextResponse)
async def update_tenant_context(
    context_update: TenantContextUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Update the current tenant's context/profile settings.
    Only provided fields are updated (partial update supported).
    """
    context = db.query(TenantContext).filter(
        TenantContext.tenant_id == tenant.tenant_id
    ).first()
    
    # Create if doesn't exist
    if not context:
        context = TenantContext(
            tenant_id=tenant.tenant_id,
            industry=Industry.OTHER,
            tone_of_voice=ToneOfVoice.PROFESSIONAL,
            language_style=LanguageStyle.CONVERSATIONAL,
            response_length=ResponseLength.BALANCED
        )
        db.add(context)
    
    # Update fields that are provided
    update_data = context_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(context, field, value)
    
    context.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(context)
    
    logger.info(f"Updated context for tenant {tenant.tenant_id}")
    return context


@router.get("/context/options")
async def get_context_options() -> Dict[str, List[Dict[str, str]]]:
    """
    Get all available options for tenant context dropdowns.
    Used to populate form select fields in the UI.
    """
    def to_label(value: str) -> str:
        """Convert enum value to human-readable label."""
        return value.replace('_', ' ').title()
    
    return {
        "industries": [
            {"value": industry.value, "label": to_label(industry.value)}
            for industry in Industry
        ],
        "tones": [
            {"value": tone.value, "label": to_label(tone.value)}
            for tone in ToneOfVoice
        ],
        "language_styles": [
            {"value": style.value, "label": to_label(style.value)}
            for style in LanguageStyle
        ],
        "response_lengths": [
            {"value": length.value, "label": to_label(length.value)}
            for length in ResponseLength
        ]
    }



async def get_analytics(
    days: int = 30,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get analytics data for the tenant.
    """
    # Get date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query analytics
    analytics = db.query(Analytics).filter(
        and_(
            Analytics.tenant_id == tenant.tenant_id,
            Analytics.date >= start_date
        )
    ).order_by(Analytics.date.desc()).all()
    
    return analytics


@router.get("/documents/stats")
async def get_document_stats(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get detailed document statistics.
    """
    # Total documents by status
    status_counts = db.query(
        Document.status,
        func.count(Document.id)
    ).filter(
        Document.tenant_id == tenant.tenant_id
    ).group_by(Document.status).all()
    
    # Documents uploaded by date (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    uploads_by_date = db.query(
        func.date(Document.upload_date).label('date'),
        func.count(Document.id).label('count')
    ).filter(
        and_(
            Document.tenant_id == tenant.tenant_id,
            Document.upload_date >= thirty_days_ago
        )
    ).group_by(func.date(Document.upload_date)).all()
    
    # Category distribution
    category_counts = db.query(
        Document.category,
        func.count(Document.id)
    ).filter(
        Document.tenant_id == tenant.tenant_id
    ).group_by(Document.category).all()
    
    # Vector database stats
    vector_store = get_vector_store()
    vector_stats = await vector_store.get_collection_stats(tenant.tenant_id)
    
    return {
        "status_distribution": {str(status): count for status, count in status_counts},
        "uploads_by_date": [
            {"date": str(date), "count": count}
            for date, count in uploads_by_date
        ],
        "category_distribution": {
            (category or "uncategorized"): count
            for category, count in category_counts
        },
        "vector_database": vector_stats
    }


@router.get("/health", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """
    System health check for all services.
    """
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "database": "unknown",
        "qdrant": "unknown",
        "groq": "unknown",
        "timestamp": datetime.utcnow()
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        health_status["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Qdrant
    try:
        vector_store = get_vector_store()
        is_healthy = await vector_store.health_check()
        health_status["qdrant"] = "healthy" if is_healthy else "unhealthy"
        if not is_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        health_status["qdrant"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Groq API
    try:
        llm_service = get_llm_service()
        is_healthy = await llm_service.health_check()
        health_status["groq"] = "healthy" if is_healthy else "unhealthy"
        if not is_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Groq API health check failed: {e}")
        health_status["groq"] = "unhealthy"
        health_status["status"] = "degraded"
    
    return health_status


# ==================== Demo User Management ====================

@router.post("/demo-users", response_model=DemoUserResponse, status_code=status.HTTP_201_CREATED)
async def create_demo_user(
    demo_data: DemoUserCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Create a new demo user access ID for the current tenant.
    
    Product owners can generate demo IDs to share with trial users.
    """
    from app.core.security import generate_demo_id
    from datetime import timedelta
    
    # Generate unique demo ID
    demo_id = generate_demo_id()
    
    # Ensure uniqueness (very unlikely collision)
    while db.query(DemoUser).filter(DemoUser.demo_id == demo_id).first():
        demo_id = generate_demo_id()
    
    # Calculate expiration if specified
    expires_at = None
    if demo_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=demo_data.expires_in_days)
    
    # Create demo user
    demo_user = DemoUser(
        demo_id=demo_id,
        tenant_id=tenant.tenant_id,
        name=demo_data.name,
        expires_at=expires_at,
        is_active=1
    )
    
    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)
    
    logger.info(f"Demo user created: {demo_id} for tenant {tenant.tenant_id}")
    
    return DemoUserResponse(
        id=demo_user.id,
        demo_id=demo_user.demo_id,
        tenant_id=demo_user.tenant_id,
        name=demo_user.name,
        created_at=demo_user.created_at,
        expires_at=demo_user.expires_at,
        is_active=bool(demo_user.is_active),
        usage_count=demo_user.usage_count,
        last_used_at=demo_user.last_used_at
    )


@router.get("/demo-users", response_model=List[DemoUserResponse])
async def list_demo_users(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    List all demo users for the current tenant.
    """
    demo_users = db.query(DemoUser).filter(
        DemoUser.tenant_id == tenant.tenant_id
    ).order_by(DemoUser.created_at.desc()).all()
    
    return demo_users


@router.delete("/demo-users/{demo_id}")
async def delete_demo_user(
    demo_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Delete/deactivate a demo user.
    """
    demo_user = db.query(DemoUser).filter(
        DemoUser.demo_id == demo_id,
        DemoUser.tenant_id == tenant.tenant_id
    ).first()
    
    if not demo_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo user not found"
        )
    
    demo_user.is_active = 0
    db.commit()
    
    logger.info(f"Demo user deactivated: {demo_id}")
    
    return {"message": "Demo user deactivated successfully", "demo_id": demo_id}


# ==================== Phase 04: Escalation Log (A5) ====================

@router.get("/escalations", response_model=List[EscalationLogResponse])
async def list_escalations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session_id: Optional[str] = Query(None),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """
    List escalation log entries for admin review (A5).

    Returns queries that were escalated due to low confidence or abstention,
    ordered by most recent first.
    """
    q = db.query(EscalationLog).filter(
        EscalationLog.tenant_id == tenant.tenant_id
    )
    if session_id:
        q = q.filter(EscalationLog.session_id == session_id)

    records = q.order_by(EscalationLog.timestamp.desc()).offset(offset).limit(limit).all()

    return [
        EscalationLogResponse(
            id=r.id,
            session_id=r.session_id,
            tenant_id=r.tenant_id,
            query=r.query,
            query_type=r.query_type,
            top_score=r.top_score,
            reason=r.reason,
            timestamp=r.timestamp,
        )
        for r in records
    ]
