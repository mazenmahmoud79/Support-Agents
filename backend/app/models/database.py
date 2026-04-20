"""
SQLAlchemy database models for metadata storage.
Vector embeddings are stored in Qdrant, metadata is stored here.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, BigInteger, Enum as SQLEnum, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from .enums import (
    FileType, MessageRole, DocumentStatus, Industry, ToneOfVoice, LanguageStyle, ResponseLength,
    FeedbackType, QueryType, ImprovementStatus,
)

Base = declarative_base()


class Tenant(Base):
    """Tenant/Company model for multi-tenancy."""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=True)  # URL-safe identifier for public API
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Integer, default=1)
    
    # Public API settings
    allowed_domains = Column(Text, nullable=True)  # JSON list of allowed domains for CORS
    public_rate_limit = Column(Integer, default=60)  # Requests per minute per IP

    # WhatsApp integration — maps this tenant to a WhatsApp Business phone number
    whatsapp_phone_number_id = Column(String(100), unique=True, nullable=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="tenant", uselist=False)
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="tenant", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="tenant", cascade="all, delete-orphan")


class Document(Base):
    """Document metadata model."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    category = Column(String(100), nullable=True)
    chunk_count = Column(Integer, default=0)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Qdrant collection reference
    collection_name = Column(String(255), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, tenant={self.tenant_id})>"


class ChatHistory(Base):
    """Conversation history model."""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    sources = Column(Text, nullable=True)  # JSON string of source documents
    response_time = Column(Float, nullable=True)  # Seconds
    
    # Relationships
    tenant = relationship("Tenant", back_populates="chat_history")
    
    def __repr__(self):
        return f"<ChatHistory(id={self.id}, role={self.role}, tenant={self.tenant_id})>"


class Analytics(Base):
    """Usage analytics model."""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Metrics
    query_count = Column(Integer, default=0)
    total_response_time = Column(Float, default=0.0)  # Total seconds
    avg_response_time = Column(Float, default=0.0)  # Average seconds
    successful_queries = Column(Integer, default=0)
    failed_queries = Column(Integer, default=0)
    documents_uploaded = Column(Integer, default=0)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="analytics")
    

class User(Base):
    """User account model — one user owns one organization (tenant)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)   # null for Google-only accounts
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires_at = Column(DateTime, nullable=True)
    tenant_id = Column(String(100), ForeignKey("tenants.tenant_id"), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tenant={self.tenant_id})>"


class DemoUser(Base):
    """Demo user access model for simplified demo authentication."""
    __tablename__ = "demo_users"
    
    id = Column(Integer, primary_key=True, index=True)
    demo_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "DEMO-ABC123"
    tenant_id = Column(String(100), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    name = Column(String(255), nullable=True)  # Optional user name/label
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    is_active = Column(Integer, default=1)
    usage_count = Column(Integer, default=0)  # Track how many times used
    last_used_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<DemoUser(demo_id={self.demo_id}, tenant={self.tenant_id})>"


class TenantContext(Base):
    """Tenant context/profile for customizing AI responses."""
    __tablename__ = "tenant_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), ForeignKey("tenants.tenant_id"), unique=True, nullable=False, index=True)
    
    # Basic Company Info
    company_name = Column(String(255), nullable=True)  # Display name (can differ from tenant.name)
    company_description = Column(Text, nullable=True)  # Brief company description
    industry = Column(SQLEnum(Industry), default=Industry.OTHER, nullable=False)
    target_audience = Column(String(500), nullable=True)  # e.g., "Enterprise IT professionals"
    
    # Response Style Settings
    tone_of_voice = Column(SQLEnum(ToneOfVoice), default=ToneOfVoice.PROFESSIONAL, nullable=False)
    language_style = Column(SQLEnum(LanguageStyle), default=LanguageStyle.CONVERSATIONAL, nullable=False)
    response_length = Column(SQLEnum(ResponseLength), default=ResponseLength.BALANCED, nullable=False)
    
    # Branding & Messaging
    greeting_style = Column(String(500), nullable=True)  # Custom greeting
    sign_off_style = Column(String(500), nullable=True)  # Custom sign-off
    keywords_to_use = Column(Text, nullable=True)  # Preferred vocabulary (comma-separated)
    keywords_to_avoid = Column(Text, nullable=True)  # Words to avoid (comma-separated)
    unique_selling_points = Column(Text, nullable=True)  # Key differentiators
    
    # Support Contact (Fallback)
    support_email = Column(String(255), nullable=True)
    support_phone = Column(String(100), nullable=True)
    support_hours = Column(String(255), nullable=True)  # e.g., "24/7" or "Mon-Fri 9AM-6PM EST"
    support_url = Column(String(500), nullable=True)  # Link to support page
    
    # Custom Instructions
    custom_instructions = Column(Text, nullable=True)  # Additional prompt rules
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<TenantContext(tenant={self.tenant_id}, industry={self.industry})>"


# ==================== Phase 04 Models ====================

class EscalationLog(Base):
    """Logs every abstention / low-confidence escalation event."""
    __tablename__ = "escalation_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    query = Column(Text, nullable=False)
    query_type = Column(SQLEnum(QueryType), nullable=True)
    top_score = Column(Float, nullable=True)
    reason = Column(String(100), nullable=False, default="low_confidence")
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<EscalationLog(id={self.id}, tenant={self.tenant_id}, reason={self.reason})>"


class MessageFeedback(Base):
    """Captures thumbs-up / thumbs-down / agent corrections on assistant messages."""
    __tablename__ = "message_feedback"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    message_id = Column(String(100), nullable=True, index=True)  # Client-generated message ID
    feedback_type = Column(SQLEnum(FeedbackType), nullable=False)
    query = Column(Text, nullable=True)              # Original user query
    response = Column(Text, nullable=True)           # Original assistant response
    correction_text = Column(Text, nullable=True)    # Agent-supplied corrected answer
    source_documents = Column(Text, nullable=True)      # JSON snapshot of sources at feedback time
    improvement_status = Column(SQLEnum(ImprovementStatus), default=ImprovementStatus.NEEDS_REVIEW)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<MessageFeedback(id={self.id}, type={self.feedback_type}, tenant={self.tenant_id})>"


class WhatsAppSession(Base):
    """Maps a WhatsApp conversation (wa_id) to an internal tenant session."""
    __tablename__ = "whatsapp_sessions"

    id = Column(Integer, primary_key=True, index=True)
    wa_id = Column(String(50), nullable=False, index=True)       # WhatsApp sender number
    tenant_id = Column(String(100), ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False)             # Internal session_id
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<WhatsAppSession(wa_id={self.wa_id}, tenant={self.tenant_id})>"
