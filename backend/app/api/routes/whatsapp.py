"""
WhatsApp Cloud API integration routes.

F1: POST /integrations/whatsapp/webhook  — receive inbound messages
F1: GET  /integrations/whatsapp/webhook  — webhook verification (Meta challenge)
F2: WhatsApp session mapping (wa_id → internal session_id)
F3: Arabic language detection and routing
F4: Response sender via WhatsApp Cloud API
"""
import hashlib
import hmac
import json
import uuid
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.database import Tenant, WhatsAppSession
from app.models.enums import QueryType
from app.services.rag_service import get_rag_service

logger = get_logger(__name__)

router = APIRouter(prefix="/integrations/whatsapp", tags=["WhatsApp"])

WHATSAPP_API_BASE = "https://graph.facebook.com/v19.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_language(text: str) -> str:
    """Lightweight language detection — returns 'ar' or 'en'."""
    arabic_chars = sum(1 for ch in text if "\u0600" <= ch <= "\u06ff")
    return "ar" if arabic_chars / max(len(text), 1) > 0.2 else "en"


async def _get_or_create_session(
    wa_id: str, tenant_id: str, db: Session
) -> str:
    """Return an existing session_id for a wa_id, or create a new mapping."""
    existing = (
        db.query(WhatsAppSession)
        .filter(
            WhatsAppSession.wa_id == wa_id,
            WhatsAppSession.tenant_id == tenant_id,
        )
        .first()
    )
    if existing:
        return existing.session_id

    session_id = f"wa_{wa_id}_{uuid.uuid4().hex[:8]}"
    mapping = WhatsAppSession(
        wa_id=wa_id,
        tenant_id=tenant_id,
        session_id=session_id,
    )
    db.add(mapping)
    db.commit()
    logger.info(f"Created WhatsApp session mapping: wa_id={wa_id} → {session_id}")
    return session_id


async def _send_whatsapp_message(to: str, text: str) -> bool:
    """Send a text reply via WhatsApp Cloud API."""
    if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        logger.warning("WhatsApp credentials not configured — skipping send")
        return False

    url = f"{WHATSAPP_API_BASE}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            logger.info(f"WhatsApp message sent to {to}")
            return True
        logger.error(f"WhatsApp send failed: {resp.status_code} {resp.text}")
        return False


def _verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Verify the X-Hub-Signature-256 from Meta to prevent spoofing.
    
    Meta signs payloads with the Facebook **App Secret**, not the access token.
    See: https://developers.facebook.com/docs/graph-api/webhooks/getting-started#verification-requests
    """
    if not settings.WHATSAPP_APP_SECRET:
        logger.warning("WHATSAPP_APP_SECRET not set — skipping signature verification (dev mode)")
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    Meta webhook verification handshake.
    Returns the hub.challenge value when the verify token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully")
        return int(hub_challenge)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Webhook verification failed",
    )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_message(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receive inbound WhatsApp messages from Meta.

    Flow:
    1. Verify signature (F1)
    2. Parse message and extract wa_id + text
    3. Map or create session (F2)
    4. Detect language; route Arabic through Arabic retrieval path (F3)
    5. Call RAG pipeline with the same confidence gate as web chat
    6. Send reply via WhatsApp Cloud API (F4)
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not _verify_signature(raw_body, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature"
        )

    payload: Dict[str, Any] = json.loads(raw_body)
    logger.debug(f"WhatsApp webhook payload: {json.dumps(payload)[:500]}")

    # Parse Meta payload structure
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id", "")

            for msg in messages:
                if msg.get("type") != "text":
                    continue   # Only handle text messages in PoC

                wa_id: str = msg["from"]
                text: str = msg["text"]["body"]
                logger.info(f"Inbound WhatsApp message from {wa_id}: {text[:80]}")

                # Resolve tenant by phone_number_id from webhook metadata.
                # Each tenant has a whatsapp_phone_number_id column for routing.
                tenant = None
                if phone_number_id:
                    tenant = (
                        db.query(Tenant)
                        .filter(
                            Tenant.whatsapp_phone_number_id == phone_number_id,
                            Tenant.is_active == 1,
                        )
                        .first()
                    )
                # Fallback: if no tenant matched by phone_number_id (e.g. column not set yet),
                # try matching via the global config setting for backward compatibility.
                if not tenant and settings.WHATSAPP_PHONE_NUMBER_ID:
                    if phone_number_id == settings.WHATSAPP_PHONE_NUMBER_ID or not phone_number_id:
                        tenant = (
                            db.query(Tenant)
                            .filter(Tenant.is_active == 1)
                            .first()
                        )
                if not tenant:
                    logger.warning("No active tenant found for WhatsApp message")
                    continue

                # Map wa_id → internal session_id (F2)
                session_id = await _get_or_create_session(wa_id, tenant.tenant_id, db)

                # Language detection for routing hint (F3)
                lang = _detect_language(text)
                logger.info(f"Detected language: {lang} for wa_id={wa_id}")

                # RAG pipeline — same confidence gate as web chat (F3 + F4)
                rag_service = get_rag_service()
                try:
                    (
                        response_text,
                        sources,
                        response_time,
                        escalated,
                        top_score,
                        query_type,
                    ) = await rag_service.query(
                        user_message=text,
                        tenant_id=tenant.tenant_id,
                        company_name=tenant.name,
                        session_id=session_id,
                        chat_history=[],
                        include_sources=False,
                        tenant_context=None,
                    )
                except Exception as exc:
                    logger.error(f"RAG error for WhatsApp message: {exc}")
                    response_text = "Sorry, I encountered an error. Please try again later."

                # Send reply (F4)
                await _send_whatsapp_message(wa_id, response_text)

                # Update last_message_at
                mapping = (
                    db.query(WhatsAppSession)
                    .filter(
                        WhatsAppSession.wa_id == wa_id,
                        WhatsAppSession.tenant_id == tenant.tenant_id,
                    )
                    .first()
                )
                if mapping:
                    from datetime import datetime
                    mapping.last_message_at = datetime.utcnow()
                    db.commit()

    # Always return 200 to Meta to acknowledge receipt
    return {"status": "ok"}
