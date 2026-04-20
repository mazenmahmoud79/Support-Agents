"""
Email service using Resend.com for transactional emails.
"""
import asyncio
from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _send_email_sync(to_email: str, subject: str, html: str) -> None:
    """Synchronous email send — runs inside a thread pool."""
    import resend
    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send({
        "from": settings.RESEND_FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html,
    })


async def send_verification_email(to_email: str, token: str) -> None:
    """Send account verification email with a one-time link."""
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured — skipping verification email")
        return

    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;padding:32px;">
      <h2 style="color:#6366f1;">Verify your email — Zada.AI</h2>
      <p>Thanks for signing up! Click the button below to verify your email address
         and access your dashboard.</p>
      <a href="{verification_url}"
         style="display:inline-block;margin:24px 0;padding:12px 28px;background:#6366f1;
                color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">
        Verify Email
      </a>
      <p style="color:#888;font-size:13px;">
        This link expires in 24 hours. If you didn't create an account, you can safely
        ignore this email.
      </p>
      <p style="color:#888;font-size:13px;">
        Or copy this link: {verification_url}
      </p>
    </div>
    """
    try:
        await asyncio.to_thread(_send_email_sync, to_email, "Verify your email — Zada.AI", html)
        logger.info(f"Verification email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {to_email}: {e}")
        raise


async def send_welcome_email(to_email: str, org_name: str) -> None:
    """Send welcome email after successful verification."""
    if not settings.RESEND_API_KEY:
        return

    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto;padding:32px;">
      <h2 style="color:#6366f1;">Welcome to Zada.AI, {org_name}!</h2>
      <p>Your email is verified and your organization is ready. Head to your dashboard to
         upload documents and configure your AI support agent.</p>
      <a href="{settings.FRONTEND_URL}"
         style="display:inline-block;margin:24px 0;padding:12px 28px;background:#6366f1;
                color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">
        Go to Dashboard
      </a>
    </div>
    """
    try:
        await asyncio.to_thread(_send_email_sync, to_email, f"Welcome to Zada.AI — {org_name}", html)
    except Exception as e:
        logger.warning(f"Failed to send welcome email to {to_email}: {e}")
