"""
Chat routes for RAG-powered conversational AI.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.session import get_db
from app.api.deps import get_current_tenant
from app.models.database import Tenant, ChatHistory, Analytics, TenantContext, EscalationLog
from app.models.schemas import ChatRequest, ChatResponse, ConversationHistory, SourceDocument
from app.models.enums import MessageRole
from app.services.rag_service import get_rag_service
from app.core.logging import get_logger
from datetime import datetime
import json
import asyncio

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Send a message and get an AI-powered response.
    
    Uses RAG to retrieve relevant context from the knowledge base.
    """
    logger.info(f"Chat request from tenant {tenant.tenant_id}: {request.message[:50]}")
    
    start_time = datetime.utcnow()
    
    # Get conversation history
    history_records = db.query(ChatHistory).filter(
        and_(
            ChatHistory.tenant_id == tenant.tenant_id,
            ChatHistory.session_id == request.session_id
        )
    ).order_by(ChatHistory.timestamp.desc()).limit(10).all()
    
    # Format history for RAG service
    chat_history = [
        {"role": record.role.value, "content": record.content}
        for record in reversed(history_records)
    ]
    
    # Load tenant context for customization
    tenant_context_record = db.query(TenantContext).filter(
        TenantContext.tenant_id == tenant.tenant_id
    ).first()
    
    # Convert to dict for RAG service (or None if not exists)
    tenant_context = None
    if tenant_context_record:
        tenant_context = {
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
    
    # Get RAG service
    rag_service = get_rag_service()
    
    try:
        # Execute RAG pipeline with tenant context
        response_text, sources, response_time, escalated, top_score, query_type = await rag_service.query(
            user_message=request.message,
            tenant_id=tenant.tenant_id,
            company_name=tenant.name,
            session_id=request.session_id,
            chat_history=chat_history,
            include_sources=request.include_sources,
            tenant_context=tenant_context
        )
        
        # Save user message to history
        user_message = ChatHistory(
            tenant_id=tenant.tenant_id,
            session_id=request.session_id,
            role=MessageRole.USER,
            content=request.message,
            timestamp=start_time
        )
        db.add(user_message)
        
        # Save assistant response to history
        assistant_message = ChatHistory(
            tenant_id=tenant.tenant_id,
            session_id=request.session_id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            sources=json.dumps(sources) if sources else None,
            response_time=response_time
        )
        db.add(assistant_message)

        # Log escalation event if confidence gate triggered
        if escalated:
            escalation = EscalationLog(
                tenant_id=tenant.tenant_id,
                session_id=request.session_id,
                query=request.message,
                query_type=query_type,
                top_score=top_score,
                reason="low_confidence",
            )
            db.add(escalation)
        
        # Update analytics
        today = datetime.utcnow().date()
        analytics = db.query(Analytics).filter(
            and_(
                Analytics.tenant_id == tenant.tenant_id,
                Analytics.date >= today
            )
        ).first()
        
        if not analytics:
            analytics = Analytics(
                tenant_id=tenant.tenant_id,
                date=datetime.utcnow()
            )
            db.add(analytics)
        
        analytics.query_count = (analytics.query_count or 0) + 1
        analytics.successful_queries = (analytics.successful_queries or 0) + 1
        analytics.total_response_time = (analytics.total_response_time or 0.0) + response_time
        analytics.avg_response_time = analytics.total_response_time / analytics.query_count
        
        db.commit()
        
        # Format sources for response
        source_documents = None
        if request.include_sources and sources:
            source_documents = [
                SourceDocument(**source)
                for source in sources
            ]
        
        logger.info(f"Chat response generated in {response_time:.2f}s")
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            sources=source_documents,
            response_time=response_time,
            timestamp=datetime.utcnow(),
            escalated=escalated,
            confidence_score=top_score,
        )
    
    except Exception as e:
        logger.error(f"Error generating chat response: {e}")
        
        # Update failed analytics
        today = datetime.utcnow().date()
        analytics = db.query(Analytics).filter(
            and_(
                Analytics.tenant_id == tenant.tenant_id,
                Analytics.date >= today
            )
        ).first()
        
        if analytics:
            analytics.failed_queries = (analytics.failed_queries or 0) + 1
            db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {str(e)}"
        )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Send a message and get a streaming AI response.
    
    Returns Server-Sent Events (SSE) for real-time streaming.
    """
    logger.info(f"Streaming chat request from tenant {tenant.tenant_id}")
    
    # Get conversation history
    history_records = db.query(ChatHistory).filter(
        and_(
            ChatHistory.tenant_id == tenant.tenant_id,
            ChatHistory.session_id == request.session_id
        )
    ).order_by(ChatHistory.timestamp.desc()).limit(10).all()
    
    chat_history = [
        {"role": record.role.value, "content": record.content}
        for record in reversed(history_records)
    ]
    
    # Load tenant context for customization
    tenant_context_record = db.query(TenantContext).filter(
        TenantContext.tenant_id == tenant.tenant_id
    ).first()
    
    # Convert to dict for RAG service (or None if not exists)
    tenant_context = None
    if tenant_context_record:
        tenant_context = {
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
    
    # Get RAG service
    rag_service = get_rag_service()
    
    async def generate_stream():
        """Generator for SSE streaming."""
        start_time = datetime.utcnow()
        full_response = []
        sources = []
        
        try:
            # Stream RAG response with tenant context
            async for chunk, chunk_sources, is_final, escalated, top_score, query_type in rag_service.query_stream(
                user_message=request.message,
                tenant_id=tenant.tenant_id,
                company_name=tenant.name,
                session_id=request.session_id,
                chat_history=chat_history,
                tenant_context=tenant_context
            ):
                if chunk:
                    full_response.append(chunk)
                    # Send chunk as SSE
                    yield f"data: {json.dumps({'content': chunk, 'is_final': False})}\n\n"
                
                if is_final and chunk_sources:
                    sources = chunk_sources
            
            # Calculate response time
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            # Save conversation to database
            user_message = ChatHistory(
                tenant_id=tenant.tenant_id,
                session_id=request.session_id,
                role=MessageRole.USER,
                content=request.message,
                timestamp=start_time
            )
            db.add(user_message)
            
            complete_response = "".join(full_response)
            assistant_message = ChatHistory(
                tenant_id=tenant.tenant_id,
                session_id=request.session_id,
                role=MessageRole.ASSISTANT,
                content=complete_response,
                sources=json.dumps(sources) if sources else None,
                response_time=response_time
            )
            db.add(assistant_message)
            
            # Update analytics
            today = datetime.utcnow().date()
            analytics = db.query(Analytics).filter(
                and_(
                    Analytics.tenant_id == tenant.tenant_id,
                    Analytics.date >= today
                )
            ).first()
            
            if not analytics:
                analytics = Analytics(
                    tenant_id=tenant.tenant_id, 
                    date=datetime.utcnow(),
                    query_count=0,
                    successful_queries=0,
                    failed_queries=0,
                    total_response_time=0.0
                )
                db.add(analytics)
            
            analytics.query_count = (analytics.query_count or 0) + 1
            analytics.successful_queries = (analytics.successful_queries or 0) + 1
            analytics.total_response_time = (analytics.total_response_time or 0.0) + response_time
            analytics.avg_response_time = analytics.total_response_time / analytics.query_count
            
            db.commit()

            # Log escalation in streaming path (same as non-stream)
            if escalated:
                escalation = EscalationLog(
                    tenant_id=tenant.tenant_id,
                    session_id=request.session_id,
                    query=request.message,
                    query_type=query_type,
                    top_score=top_score,
                    reason="low_confidence",
                )
                db.add(escalation)
                db.commit()
            
            # Send final message with sources
            final_data = {
                "content": "",
                "is_final": True,
                "sources": sources if request.include_sources else None,
                "response_time": response_time,
                "escalated": escalated,
                "confidence_score": top_score,
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            error_data = {"error": str(e), "is_final": True}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/history/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(
    session_id: str,
    limit: int = 50,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get conversation history for a session.
    """
    messages = db.query(ChatHistory).filter(
        and_(
            ChatHistory.tenant_id == tenant.tenant_id,
            ChatHistory.session_id == session_id
        )
    ).order_by(ChatHistory.timestamp.asc()).limit(limit).all()
    
    formatted_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    
    return ConversationHistory(
        session_id=session_id,
        messages=formatted_messages
    )


@router.delete("/history/{session_id}")
async def clear_conversation_history(
    session_id: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Clear conversation history for a session.
    """
    deleted = db.query(ChatHistory).filter(
        and_(
            ChatHistory.tenant_id == tenant.tenant_id,
            ChatHistory.session_id == session_id
        )
    ).delete()
    
    db.commit()
    
    logger.info(f"Cleared {deleted} messages from session {session_id}")
    
    return {"message": f"Deleted {deleted} messages"}
