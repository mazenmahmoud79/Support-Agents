"""
Configuration management for the AI Customer Service System.
Loads settings from environment variables with validation.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "AI Customer Service System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API Configuration
    API_V1_PREFIX: str = "/api"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    SUPER_ADMIN_PASSWORD: Optional[str] = None  # Required in production
    
    # Database
    DATABASE_URL: str
    
    # Qdrant Vector Database
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_PREFIX: str = "tenant_"
    
    # Groq LLM
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FALLBACK_MODEL: str = "mixtral-8x7b-32768"
    GROQ_MAX_TOKENS: int = 1024
    GROQ_TEMPERATURE: float = 0.7
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Document Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".csv"}
    
    # RAG Configuration
    SIMILARITY_THRESHOLD: float = 0.1
    TOP_K_RESULTS: int = 5
    MAX_CONTEXT_LENGTH: int = 4000
    CONVERSATION_HISTORY_LENGTH: int = 5
    ENABLE_RERANKING: bool = True  # Enable cross-encoder re-ranking
    RERANK_TOP_K: int = 8  # Number of chunks to keep after re-ranking

    # Phase 04: Hybrid Retrieval & Trust Engine
    ENABLE_BM25: bool = True                  # Run BM25 alongside dense retrieval
    BM25_TOP_K: int = 10                      # BM25 candidates before RRF fusion
    RRF_K: int = 60                           # Reciprocal Rank Fusion constant
    ABSTENTION_THRESHOLD: float = 0.35        # Below this top rerank score → escalate
    CONFIDENCE_MODERATE_THRESHOLD: float = 0.55  # Below this → show uncertainty language

    # Phase 04: WhatsApp Integration
    WHATSAPP_TOKEN: Optional[str] = None      # WhatsApp Cloud API access token
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None  # Webhook verify token
    WHATSAPP_APP_SECRET: Optional[str] = None  # Facebook App Secret for webhook signature verification
    
    # Redis (optional)
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    # Email (Resend.com)
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM_EMAIL: str = "noreply@yourdomain.com"

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None

    # Frontend URL (for email verification links)
    FRONTEND_URL: str = "http://localhost:5173"
    
    model_config = SettingsConfigDict(
        env_file="../.env",  # Look in parent directory for local dev
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()


def validate_production_config():
    """
    Validate critical configuration for production.
    Call on startup; raises RuntimeError if unsafe defaults detected.
    """
    errors = []
    if not settings.DEBUG:
        if not settings.SUPER_ADMIN_PASSWORD or settings.SUPER_ADMIN_PASSWORD == "admin123":
            errors.append("SUPER_ADMIN_PASSWORD must be set to a strong value in production")
        if settings.SECRET_KEY in ("changeme", "your_secret_key_change_this_to_random_string"):
            errors.append("SECRET_KEY must be changed from default")
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.startswith("gsk_EXAMPLE"):
            errors.append("GROQ_API_KEY must be set")
    if errors:
        raise RuntimeError("Production configuration errors:\n  - " + "\n  - ".join(errors))
