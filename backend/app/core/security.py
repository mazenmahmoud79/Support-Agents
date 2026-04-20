"""
Security utilities for authentication and authorization.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key() -> str:
    """
    Generate a secure random API key.
    
    Returns:
        str: Random API key (32 bytes hex)
    """
    return secrets.token_urlsafe(32)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash.
    
    Args:
        plain_key: Plain text API key
        hashed_key: Hashed API key
    
    Returns:
        bool: True if key matches, False otherwise
    """
    return pwd_context.verify(plain_key, hashed_key)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.
    
    Args:
        api_key: Plain text API key
    
    Returns:
        str: Hashed API key
    """
    return pwd_context.hash(api_key)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
    
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
    
    Returns:
        Optional[dict]: Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_tenant_id(name: str) -> str:
    """
    Generate a unique tenant ID from company name.
    
    Args:
        name: Company name
    
    Returns:
        str: Tenant ID
    """
    # Create a slug from company name and add random suffix
    slug = name.lower().replace(" ", "_").replace("-", "_")
    # Remove non-alphanumeric characters
    slug = ''.join(c for c in slug if c.isalnum() or c == '_')
    # Add random suffix
    suffix = secrets.token_hex(4)
    return f"{slug}_{suffix}"


def generate_demo_id() -> str:
    """
    Generate a simple, memorable demo access ID.
    
    Format: DEMO-XXXXXX (where X is alphanumeric)
    
    Returns:
        str: Demo ID
    """
    # Generate 6 character code using uppercase letters and numbers
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choice(chars) for _ in range(6))
    return f"DEMO-{code}"