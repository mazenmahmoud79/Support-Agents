"""
Database session management using SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency function to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models, then applies incremental
    migrations for columns/enum values added after initial schema creation.
    """
    from app.models.database import Base
    Base.metadata.create_all(bind=engine)
    _apply_phase04_migrations()


def _apply_phase04_migrations():
    """
    Apply Phase 04 schema changes that CREATE TABLE cannot handle on
    an existing PostgreSQL database (new enum values, new columns).
    All statements are idempotent — safe to run on every startup.
    """
    from sqlalchemy import text, inspect

    with engine.connect() as conn:
        # 1. Add new DocumentStatus enum values
        for val in ("DRAFT", "ACTIVE", "ARCHIVED", "DEPRECATED"):
            try:
                conn.execute(text(
                    f"ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS '{val}'"
                ))
            except Exception:
                pass  # value already exists or DB is SQLite (dev)

        # 2. Add whatsapp_phone_number_id column to tenants
        inspector = inspect(engine)
        tenant_cols = {c["name"] for c in inspector.get_columns("tenants")}
        if "whatsapp_phone_number_id" not in tenant_cols:
            try:
                conn.execute(text(
                    "ALTER TABLE tenants ADD COLUMN whatsapp_phone_number_id VARCHAR(100) UNIQUE"
                ))
            except Exception:
                pass

        conn.commit()
