"""
Public Chat API routes for website embedding.
These endpoints require API token authentication via X-API-Token header.
"""
import json
import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.database import Tenant, ChatHistory, TenantContext
from app.models.enums import MessageRole
from app.services.rag_service import get_rag_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/public", tags=["public-chat"])


class PublicChatRequest(BaseModel):
    """Request model for public chat."""
    message: str
    session_id: Optional[str] = None


class PublicChatResponse(BaseModel):
    """Response model for public chat."""
    response: str
    sources: list = []
    session_id: str


def get_tenant_by_slug(slug: str, db: Session) -> Optional[Tenant]:
    """Get tenant by slug."""
    return db.query(Tenant).filter(Tenant.slug == slug, Tenant.is_active == 1).first()


def validate_api_token(tenant: Tenant, api_token: Optional[str]) -> bool:
    """
    Validate the API token against the tenant's API key.
    
    Args:
        tenant: The tenant object
        api_token: The token from X-API-Token header
        
    Returns:
        True if valid, raises HTTPException if invalid
    """
    if not api_token:
        logger.warning(f"Missing API token for tenant {tenant.tenant_id}")
        raise HTTPException(
            status_code=401,
            detail="Missing API token. Include X-API-Token header.",
            headers={"WWW-Authenticate": "X-API-Token"}
        )
    
    if api_token != tenant.api_key:
        logger.warning(f"Invalid API token for tenant {tenant.tenant_id}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API token.",
            headers={"WWW-Authenticate": "X-API-Token"}
        )
    
    return True


def get_tenant_context_dict(tenant_context_record) -> Optional[dict]:
    """Convert tenant context record to dictionary for RAG service."""
    if not tenant_context_record:
        return None
    
    return {
        'company_name': tenant_context_record.company_name,
        'company_description': tenant_context_record.company_description,
        'industry': tenant_context_record.industry.value if tenant_context_record.industry else 'other',
        'target_audience': tenant_context_record.target_audience,
        'tone_of_voice': tenant_context_record.tone_of_voice.value if tenant_context_record.tone_of_voice else 'professional',
        'language_style': tenant_context_record.language_style.value if tenant_context_record.language_style else 'conversational',
        'response_length': tenant_context_record.response_length.value if tenant_context_record.response_length else 'balanced',
        'greeting_style': tenant_context_record.greeting_style,
        'sign_off_style': tenant_context_record.sign_off_style,
        'keywords_to_use': tenant_context_record.keywords_to_use,
        'keywords_to_avoid': tenant_context_record.keywords_to_avoid,
        'unique_selling_points': tenant_context_record.unique_selling_points,
        'support_email': tenant_context_record.support_email,
        'support_phone': tenant_context_record.support_phone,
        'support_hours': tenant_context_record.support_hours,
        'support_url': tenant_context_record.support_url,
        'custom_instructions': tenant_context_record.custom_instructions,
    }


@router.post("/chat/{tenant_slug}", response_model=PublicChatResponse)
async def public_chat(
    tenant_slug: str,
    request: PublicChatRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    x_api_token: Optional[str] = Header(None, alias="X-API-Token")
):
    """
    Public chat endpoint for website embedding.
    
    Requires X-API-Token header with valid API token for authentication.
    The token is generated from the Integration page in the admin dashboard.
    """
    logger.info(f"Public chat request for tenant slug: {tenant_slug}")
    
    # Get tenant by slug
    tenant = get_tenant_by_slug(tenant_slug, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    # Validate API token
    validate_api_token(tenant, x_api_token)
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Load tenant context for customization
    tenant_context_record = db.query(TenantContext).filter(
        TenantContext.tenant_id == tenant.tenant_id
    ).first()
    
    tenant_context = get_tenant_context_dict(tenant_context_record)
    
    # Get RAG service and process query
    rag_service = get_rag_service()
    
    try:
        response, sources, response_time, escalated, top_score, query_type = await rag_service.query(
            user_message=request.message,
            tenant_id=tenant.tenant_id,
            company_name=tenant.name,
            session_id=session_id,
            include_sources=True,
            tenant_context=tenant_context
        )
        
        logger.info(f"Public chat response generated for {tenant_slug} in {response_time:.2f}s (escalated={escalated})")
        
        return PublicChatResponse(
            response=response,
            sources=sources,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error in public chat for {tenant_slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response")


@router.post("/chat/{tenant_slug}/stream")
async def public_chat_stream(
    tenant_slug: str,
    request: PublicChatRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    x_api_token: Optional[str] = Header(None, alias="X-API-Token")
):
    """
    Streaming public chat endpoint for website embedding.
    Returns Server-Sent Events (SSE) for real-time response.
    
    Requires X-API-Token header with valid API token for authentication.
    """
    logger.info(f"Public chat stream request for tenant slug: {tenant_slug}")
    
    # Get tenant by slug
    tenant = get_tenant_by_slug(tenant_slug, db)
    if not tenant:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    # Validate API token
    validate_api_token(tenant, x_api_token)
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Load tenant context for customization
    tenant_context_record = db.query(TenantContext).filter(
        TenantContext.tenant_id == tenant.tenant_id
    ).first()
    
    tenant_context = get_tenant_context_dict(tenant_context_record)
    
    # Get RAG service
    rag_service = get_rag_service()
    
    async def generate():
        """Generate SSE stream."""
        try:
            # Send session ID first
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            
            # Stream the response with tenant context
            async for chunk, sources, is_final, escalated, top_score, query_type in rag_service.query_stream(
                user_message=request.message,
                tenant_id=tenant.tenant_id,
                company_name=tenant.name,
                session_id=session_id,
                tenant_context=tenant_context
            ):
                if is_final:
                    # Send sources at the end
                    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                    
        except Exception as e:
            logger.error(f"Error in public chat stream for {tenant_slug}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to generate response'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
