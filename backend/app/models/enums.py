"""Enumerations for the application."""
from enum import Enum


class FileType(str, Enum):
    """Supported file types for upload."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"


class MessageRole(str, Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class DocumentStatus(str, Enum):
    """Document processing status and lifecycle state."""
    # Processing pipeline states
    PENDING = "pending"
    PROCESSING = "processing"
    FAILED = "failed"
    # Knowledge lifecycle states (Phase 04)
    DRAFT = "draft"        # Processed but not yet published — awaits admin review
    ACTIVE = "active"      # Published and included in retrieval
    ARCHIVED = "archived"  # Removed from retrieval, kept for reference
    DEPRECATED = "deprecated"  # Superseded by a newer version
    # Legacy alias kept for backward compatibility
    COMPLETED = "completed"  # Treated as ACTIVE in retrieval filters


class FeedbackType(str, Enum):
    """Type of feedback on a chat response."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    AGENT_CORRECTION = "agent_correction"


class QueryType(str, Enum):
    """Classified query type used to route retrieval."""
    FAQ = "faq"
    POLICY = "policy"
    TROUBLESHOOTING = "troubleshooting"
    TABLE = "table"
    GENERAL = "general"


class ImprovementStatus(str, Enum):
    """Status of an item in the admin improvement queue."""
    NEEDS_REVIEW = "needs_review"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


# ==================== Tenant Context Enums ====================

class Industry(str, Enum):
    """Industry/sector options for tenant context."""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    ECOMMERCE = "ecommerce"
    FINANCE = "finance"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    HOSPITALITY = "hospitality"
    LEGAL = "legal"
    CONSULTING = "consulting"
    INSURANCE = "insurance"
    TELECOMMUNICATIONS = "telecommunications"
    OTHER = "other"


class ToneOfVoice(str, Enum):
    """Tone of voice options for AI responses."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    CASUAL = "casual"
    EMPATHETIC = "empathetic"
    TECHNICAL = "technical"
    ENTHUSIASTIC = "enthusiastic"


class LanguageStyle(str, Enum):
    """Language complexity style for AI responses."""
    SIMPLE = "simple"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    BUSINESS = "business"


class ResponseLength(str, Enum):
    """Preferred response length for AI."""
    CONCISE = "concise"
    BALANCED = "balanced"
    DETAILED = "detailed"
