"""
Authentication routes — register, login (email+password), Google OAuth, email verification.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import get_logger
from app.core.rate_limit import limiter, AUTH_LIMIT
from app.core.security import (
    create_access_token,
    generate_api_key,
    generate_tenant_id,
    hash_password,
    verify_password,
    verify_token,
)
from app.db.session import get_db
from app.models.database import Tenant, User
from app.models.schemas import (
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    ResendVerificationRequest,
    TokenResponse,
    UserResponse,
)
from app.services.email_service import send_verification_email, send_welcome_email

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

_VERIFICATION_TOKEN_EXPIRE_HOURS = 24


def _make_jwt(user: User) -> str:
    return create_access_token({
        "sub": str(user.id),
        "tenant_id": user.tenant_id,
        "email": user.email,
    })


def _new_verification_token() -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=_VERIFICATION_TOKEN_EXPIRE_HOURS)
    return token, expires


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_LIMIT)
async def register(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Create a new organization account. Sends a verification email."""
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create Tenant
    tenant_id = generate_tenant_id(body.org_name)
    while db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first():
        tenant_id = generate_tenant_id(body.org_name)

    tenant = Tenant(
        tenant_id=tenant_id,
        name=body.org_name,
        api_key=generate_api_key(),
        is_active=1,
    )
    db.add(tenant)
    db.flush()  # get tenant_id without full commit

    # Create User
    token, expires = _new_verification_token()
    user = User(
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
        is_verified=False,
        verification_token=token,
        verification_token_expires_at=expires,
        tenant_id=tenant_id,
    )
    db.add(user)
    db.commit()

    email_sent = False
    try:
        await send_verification_email(user.email, token)
        email_sent = True
    except Exception as exc:
        logger.warning(
            f"Could not send verification email to {user.email}: {exc}. "
            f"Verification URL: {settings.FRONTEND_URL}/verify-email?token={token}"
        )

    logger.info(f"New registration: {user.email} (org: {body.org_name}, email_sent={email_sent})")
    return {"message": "Account created. Please check your email to verify your address."}


# ---------------------------------------------------------------------------
# Verify Email
# ---------------------------------------------------------------------------

@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email address using the one-time token from the verification link."""
    user = db.query(User).filter(User.verification_token == token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    if user.verification_token_expires_at and user.verification_token_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Verification link expired. Please request a new one.",
        )

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires_at = None
    db.commit()

    try:
        await send_welcome_email(user.email, user.tenant.name)
    except Exception as exc:
        logger.warning(f"Could not send welcome email to {user.email}: {exc}")

    logger.info(f"Email verified: {user.email}")
    return TokenResponse(access_token=_make_jwt(user))


# ---------------------------------------------------------------------------
# Login (email + password)
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
@limiter.limit(AUTH_LIMIT)
async def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    """Login with email and password. Returns a JWT."""
    user = db.query(User).filter(User.email == body.email.lower()).first()

    # Constant-time rejection — don't reveal whether email exists
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please check your inbox.",
        )

    logger.info(f"Login: {user.email}")
    return TokenResponse(access_token=_make_jwt(user))


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

@router.post("/google", response_model=TokenResponse)
@limiter.limit(AUTH_LIMIT)
async def google_auth(
    request: Request,
    body: GoogleAuthRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate via Google. Receives a Google ID token from the frontend
    (@react-oauth/google), verifies it with Google, then creates or logs in the user.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google login is not configured")

    # Verify the Google ID token
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": body.credential},
            timeout=10,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google credential")

    info = resp.json()

    if info.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Google token audience mismatch")

    if info.get("email_verified") != "true":
        raise HTTPException(status_code=400, detail="Google account email is not verified")

    google_id = info["sub"]
    email = info["email"].lower()
    name = info.get("name", email.split("@")[0])

    # Try to find existing user by google_id or email
    user = db.query(User).filter(User.google_id == google_id).first()

    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Link Google to existing email account
            user.google_id = google_id
            user.is_verified = True
            db.commit()
        else:
            # New user — create Tenant + User
            tenant_id = generate_tenant_id(name)
            while db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first():
                tenant_id = generate_tenant_id(name)

            tenant = Tenant(
                tenant_id=tenant_id,
                name=name,
                api_key=generate_api_key(),
                is_active=1,
            )
            db.add(tenant)
            db.flush()

            user = User(
                email=email,
                google_id=google_id,
                is_verified=True,   # Google accounts are pre-verified
                tenant_id=tenant_id,
            )
            db.add(user)
            db.commit()
            logger.info(f"New Google signup: {email}")

    logger.info(f"Google login: {email}")
    return TokenResponse(access_token=_make_jwt(user))


# ---------------------------------------------------------------------------
# Resend Verification
# ---------------------------------------------------------------------------

@router.post("/resend-verification")
@limiter.limit(AUTH_LIMIT)
async def resend_verification(
    request: Request,
    body: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    """Resend the email verification link."""
    user = db.query(User).filter(User.email == body.email.lower()).first()

    # Don't reveal whether the email exists
    if user and not user.is_verified:
        token, expires = _new_verification_token()
        user.verification_token = token
        user.verification_token_expires_at = expires
        db.commit()
        try:
            await send_verification_email(user.email, token)
        except Exception as exc:
            logger.warning(
                f"Could not resend verification email to {user.email}: {exc}. "
                f"Verification URL: {settings.FRONTEND_URL}/verify-email?token={token}"
            )

    return {"message": "If your email is registered and unverified, a new link has been sent."}


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserResponse)
async def get_me(
    token: Optional[str] = None,
    db: Session = Depends(get_db),
    request: Request = None,
):
    """Return the current authenticated user + tenant. Reads JWT from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_token(auth_header[7:])
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

