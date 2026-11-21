"""Meta WhatsApp Inbound Webhook routes."""
import hmac
import hashlib
import json
from typing import Optional
from fastapi import APIRouter, Request, Response, Query, Header, HTTPException, status
from src.config import settings
from src.store.memory_store import memory_store

router = APIRouter(prefix="/webhooks", tags=["Inbound Webhooks"])


@router.get("/whatsapp", summary="Meta Webhook Handshake Verification")
async def verify_webhook_handshake(
    hub_mode: str = Query(..., alias="hub.mode", description="Mode, must be 'subscribe'"),
    hub_challenge: str = Query(..., alias="hub.challenge", description="Challenge integer to return"),
    hub_verify_token: str = Query(..., alias="hub.verify_token", description="Configured verify token"),
) -> Response:
    """Verifies webhook subscription handshake from Meta WhatsApp Cloud API."""
    if hub_mode == "subscribe" and hmac.compare_digest(hub_verify_token, settings.WEBHOOK_VERIFY_TOKEN):
        return Response(content=hub_challenge, media_type="text/plain", status_code=status.HTTP_200_OK)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token or mode mismatch",
    )


@router.post("/whatsapp", summary="Master Event Ingestion Router")
async def handle_inbound_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
) -> dict:
    """Ingests incoming WhatsApp events (messages, button clicks, statuses, quality updates)."""
    raw_body = await request.body()

    # Verify HMAC-SHA256 signature if header is provided
    if x_hub_signature_256:
        expected_prefix = "sha256="
        if not x_hub_signature_256.startswith(expected_prefix):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature header format. Must start with sha256=",
            )
        provided_sig = x_hub_signature_256[len(expected_prefix):]
        computed_sig = hmac.new(
            key=settings.APP_SECRET.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(provided_sig, computed_sig):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HMAC signature verification failed",
            )

    # Increment telemetry
    memory_store.increment_metric("inbound_webhooks_total")

    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        payload = {}

    if not isinstance(payload, dict):
        return {"status": "EVENT_RECEIVED", "success": True}

    # Event routing inspection with defensive type checks
    entries = payload.get("entry")
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            changes = entry.get("changes")
            if not isinstance(changes, list):
                continue
            for change in changes:
                if not isinstance(change, dict):
                    continue
                field = change.get("field")
                val = change.get("value")
                if not isinstance(val, dict):
                    continue

                # Quality Update
                if field == "phone_number_quality_update":
                    phone_id = val.get("phone_number") or entry.get("id") or settings.DEFAULT_PHONE_NUMBER_ID
                    new_rating = val.get("quality_rating")
                    if new_rating:
                        memory_store.set_quality_rating(str(phone_id), str(new_rating))

                # Messages & Opt-Outs
                if field == "messages":
                    messages = val.get("messages")
                    if isinstance(messages, list):
                        for msg in messages:
                            if not isinstance(msg, dict):
                                continue
                            # Check for opt-out keywords
                            text_body = ""
                            if msg.get("type") == "text":
                                text_obj = msg.get("text")
                                if isinstance(text_obj, dict):
                                    text_body = str(text_obj.get("body", "")).strip().upper()
                            elif msg.get("type") == "interactive":
                                interactive_obj = msg.get("interactive")
                                if isinstance(interactive_obj, dict):
                                    button_reply = interactive_obj.get("button_reply")
                                    if isinstance(button_reply, dict):
                                        text_body = str(button_reply.get("id", "")).strip().upper()

                            if text_body in ("STOP", "UNSUBSCRIBE", "OPT_OUT", "OPTOUT", "CANCEL"):
                                memory_store.increment_metric("opt_out_events_total")

    return {"status": "EVENT_RECEIVED", "success": True}
