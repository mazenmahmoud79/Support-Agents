"""
Feedback routes for capturing thumbs-up / thumbs-down and agent corrections.

B2: POST /chat/feedback
B2: POST /chat/feedback/correction
B2: GET  /admin/feedback
B3: GET  /admin/feedback/improvement-queue
B3: PATCH /admin/feedback/{feedback_id}/status
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.session import get_db
from app.api.deps import get_current_tenant
from app.models.database import Tenant, MessageFeedback
from app.models.schemas import (
    FeedbackRequest,
    AgentCorrectionRequest,
    FeedbackResponse,
    ImprovementQueueItem,
)
from app.models.enums import FeedbackType, ImprovementStatus
from app.core.logging import get_logger
from datetime import datetime
import json

logger = get_logger(__name__)

router = APIRouter(tags=["Feedback"])


# ---------------------------------------------------------------------------
# Customer / agent feedback submission
# ---------------------------------------------------------------------------

@router.post("/chat/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """
    Submit thumbs-up or thumbs-down feedback on an assistant response.
    Negative feedback is immediately flagged as NEEDS_REVIEW in the improvement queue.
    """
    improvement_status = (
        ImprovementStatus.NEEDS_REVIEW
        if request.feedback_type == FeedbackType.THUMBS_DOWN
        else ImprovementStatus.RESOLVED
    )

    feedback = MessageFeedback(
        tenant_id=tenant.tenant_id,
        session_id=request.session_id,
        message_id=request.message_id,
        feedback_type=request.feedback_type,
        query=request.query,
        response=request.response,
        source_documents=json.dumps(request.source_documents) if request.source_documents else None,
        improvement_status=improvement_status,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    logger.info(
        f"Feedback recorded: {request.feedback_type} for session {request.session_id} "
        f"tenant={tenant.tenant_id}"
    )
    return feedback


@router.post(
    "/chat/feedback/correction",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_agent_correction(
    request: AgentCorrectionRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """
    Submit an agent-corrected answer for a message.
    Marks the item as IN_PROGRESS for admin review.
    """
    feedback = MessageFeedback(
        tenant_id=tenant.tenant_id,
        session_id=request.session_id,
        message_id=request.message_id,
        feedback_type=FeedbackType.AGENT_CORRECTION,
        query=request.original_query,
        response=request.original_response,
        correction_text=request.corrected_response,
        source_documents=json.dumps(request.source_documents) if request.source_documents else None,
        improvement_status=ImprovementStatus.IN_PROGRESS,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    logger.info(
        f"Agent correction submitted for session {request.session_id} "
        f"tenant={tenant.tenant_id}"
    )
    return feedback


# ---------------------------------------------------------------------------
# Admin: view feedback and improvement queue
# ---------------------------------------------------------------------------

@router.get("/admin/feedback", response_model=List[FeedbackResponse])
async def list_feedback(
    feedback_type: Optional[FeedbackType] = Query(None),
    improvement_status: Optional[ImprovementStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """List feedback items for the tenant with optional filters."""
    q = db.query(MessageFeedback).filter(
        MessageFeedback.tenant_id == tenant.tenant_id
    )
    if feedback_type:
        q = q.filter(MessageFeedback.feedback_type == feedback_type)
    if improvement_status:
        q = q.filter(MessageFeedback.improvement_status == improvement_status)
    return q.order_by(MessageFeedback.timestamp.desc()).offset(skip).limit(limit).all()


@router.get("/admin/feedback/improvement-queue", response_model=List[ImprovementQueueItem])
async def get_improvement_queue(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """
    Return all items that need human review:
    - thumbs-down responses
    - agent corrections in progress
    """
    items = (
        db.query(MessageFeedback)
        .filter(
            MessageFeedback.tenant_id == tenant.tenant_id,
            MessageFeedback.improvement_status.in_(
                [ImprovementStatus.NEEDS_REVIEW, ImprovementStatus.IN_PROGRESS]
            ),
        )
        .order_by(MessageFeedback.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items


@router.patch("/admin/feedback/{feedback_id}/status")
async def update_feedback_status(
    feedback_id: int,
    new_status: ImprovementStatus,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    """Update the improvement status of a feedback item (resolve or dismiss)."""
    item = db.query(MessageFeedback).filter(
        MessageFeedback.id == feedback_id,
        MessageFeedback.tenant_id == tenant.tenant_id,
    ).first()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    item.improvement_status = new_status
    db.commit()
    return {"id": feedback_id, "improvement_status": new_status}
