"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from .enums import (
    FileType, MessageRole, DocumentStatus, Industry, ToneOfVoice, LanguageStyle, ResponseLength,
    FeedbackType, QueryType, ImprovementStatus,
)


# ==================== Tenant Schemas ====================

class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""
    name: str = Field(..., min_length=1, max_length=255, description="Company/tenant name")


class TenantResponse(BaseModel):
    """Schema for tenant response."""
    id: int
    tenant_id: str
    name: str
    slug: Optional[str] = None  # URL-safe identifier for public API
    api_key: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class TenantContextUpdate(BaseModel):
    """Schema for updating tenant context/profile."""
    company_name: Optional[str] = Field(None, max_length=255)
    company_description: Optional[str] = None
    industry: Optional[Industry] = None
    target_audience: Optional[str] = Field(None, max_length=500)
    
    # Response Style
    tone_of_voice: Optional[ToneOfVoice] = None
    language_style: Optional[LanguageStyle] = None
    response_length: Optional[ResponseLength] = None
    
    # Branding
    greeting_style: Optional[str] = Field(None, max_length=500)
    sign_off_style: Optional[str] = Field(None, max_length=500)
    keywords_to_use: Optional[str] = None
    keywords_to_avoid: Optional[str] = None
    unique_selling_points: Optional[str] = None
    
    # Support
    support_email: Optional[str] = Field(None, max_length=255)
    support_phone: Optional[str] = Field(None, max_length=100)
    support_hours: Optional[str] = Field(None, max_length=255)
    support_url: Optional[str] = Field(None, max_length=500)
    
    # Custom
    custom_instructions: Optional[str] = None


class TenantContextResponse(BaseModel):
    """Schema for tenant context response."""
    tenant_id: str
    company_name: Optional[str]
    company_description: Optional[str]
    industry: Industry
    target_audience: Optional[str]
    
    tone_of_voice: ToneOfVoice
    language_style: LanguageStyle
    response_length: ResponseLength
    
    # Support
    support_email: Optional[str]
    support_phone: Optional[str]
    support_hours: Optional[str]
    support_url: Optional[str]
    
    custom_instructions: Optional[str]
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantLogin(BaseModel):
    """Schema for tenant login."""
    api_key: str = Field(..., description="Tenant API key")


class DemoLogin(BaseModel):
    """Schema for demo user login."""
    demo_id: str = Field(..., min_length=6, max_length=50, description="Demo access ID")


class DemoUserCreate(BaseModel):
    """Schema for creating a demo user."""
    name: Optional[str] = Field(None, max_length=255, description="Optional user label/name")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Days until expiration")


class DemoUserResponse(BaseModel):
    """Schema for demo user response."""
    id: int
    demo_id: str
    tenant_id: str
    name: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    usage_count: int
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== Document Schemas ====================

class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    document_id: int
    filename: str
    file_type: FileType
    file_size: int
    status: DocumentStatus
    message: str = "Document uploaded successfully"


class DocumentResponse(BaseModel):
    """Schema for document metadata response."""
    id: int
    tenant_id: str
    filename: str
    file_type: FileType
    file_size: int
    category: Optional[str] = None
    chunk_count: int
    upload_date: datetime
    status: DocumentStatus
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata."""
    category: Optional[str] = None
    filename: Optional[str] = None


class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete operation."""
    document_ids: List[int] = Field(..., min_items=1, description="List of document IDs to delete")


# ==================== Chat Schemas ====================

class ChatMessage(BaseModel):
    """Schema for a single chat message."""
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: str = Field(..., description="Conversation session ID")
    include_sources: bool = Field(default=True, description="Include source documents in response")


class SourceDocument(BaseModel):
    """Schema for source document attribution — Phase 04 enhanced citations."""
    source_number: Optional[int] = None
    document_id: Optional[int] = None
    filename: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    chunk_type: Optional[str] = None
    chunk_index: Optional[int] = None
    relevance_score: float
    snippet: str = Field(..., max_length=500, description="Relevant text snippet")


class ChatResponse(BaseModel):
    """Schema for chat response."""
    response: str
    session_id: str
    sources: Optional[List[SourceDocument]] = None
    response_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    escalated: bool = False
    confidence_score: Optional[float] = None


class StreamChunk(BaseModel):
    """Schema for streaming response chunk."""
    content: str
    is_final: bool = False
    sources: Optional[List[SourceDocument]] = None


class ConversationHistory(BaseModel):
    """Schema for conversation history."""
    session_id: str
    messages: List[ChatMessage]
    
    class Config:
        from_attributes = True


# ==================== Analytics Schemas ====================

class AnalyticsResponse(BaseModel):
    """Schema for analytics data."""
    tenant_id: str
    date: datetime
    query_count: int
    avg_response_time: float
    successful_queries: int
    failed_queries: int
    documents_uploaded: int
    
    class Config:
        from_attributes = True


class DocumentStats(BaseModel):
    """Schema for document statistics."""
    total_documents: int
    total_chunks: int
    total_size_bytes: int
    documents_by_type: Dict[str, int]
    recent_uploads: List[DocumentResponse]


# ==================== System Schemas ====================

class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str
    version: str
    database: str
    qdrant: str
    groq: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Schema for error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== Phase 04 Schemas ====================

class FeedbackRequest(BaseModel):
    """Schema for submitting thumbs-up / thumbs-down on a chat message."""
    session_id: str
    message_id: Optional[str] = None
    feedback_type: FeedbackType
    query: Optional[str] = None
    response: Optional[str] = None
    source_documents: Optional[List[Dict[str, Any]]] = None


class AgentCorrectionRequest(BaseModel):
    """Schema for an agent submitting a corrected answer."""
    session_id: str
    message_id: Optional[str] = None
    original_query: Optional[str] = None
    original_response: Optional[str] = None
    corrected_response: str = Field(..., min_length=1)
    source_documents: Optional[List[Dict[str, Any]]] = None


class FeedbackResponse(BaseModel):
    """Schema for feedback submission response."""
    id: int
    feedback_type: FeedbackType
    improvement_status: ImprovementStatus
    timestamp: datetime

    class Config:
        from_attributes = True


class EscalationLogResponse(BaseModel):
    """Schema for an escalation log entry."""
    id: int
    tenant_id: str
    session_id: str
    query: str
    query_type: Optional[QueryType]
    top_score: Optional[float]
    reason: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ImprovementQueueItem(BaseModel):
    """Schema for an item in the admin improvement queue."""
    id: int
    tenant_id: str
    session_id: str
    feedback_type: FeedbackType
    improvement_status: ImprovementStatus
    correction_text: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class DocumentLifecycleResponse(BaseModel):
    """Schema for document publish/archive action response."""
    document_id: int
    filename: str
    status: DocumentStatus
    message: str


class DocumentDetailStats(BaseModel):
    """Per-document detailed stats shown in admin preview before publish."""
    document_id: int
    filename: str
    status: DocumentStatus
    chunk_count: int
    file_type: str
    file_size: int
    upload_date: datetime
    language_distribution: Dict[str, int] = {}
    chunk_type_breakdown: Dict[str, int] = {}
    parsing_warnings: List[str] = []
    page_count: Optional[int] = None


class WhatsAppWebhookPayload(BaseModel):
    """Schema for incoming WhatsApp Cloud API webhook payload."""
    object: str
    entry: List[Dict[str, Any]]


class WhatsAppSessionResponse(BaseModel):
    """Schema for WhatsApp session info."""
    wa_id: str
    tenant_id: str
    session_id: str
    created_at: datetime
    last_message_at: datetime

    class Config:
        from_attributes = True
