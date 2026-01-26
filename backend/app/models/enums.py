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
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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
