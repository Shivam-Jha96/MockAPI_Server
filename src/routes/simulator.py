"""Developer Simulation & Testing Endpoints."""
import time
import uuid
import hmac
import hashlib
import json
from typing import Optional, List, Dict, Any, Literal, Tuple
from fastapi import APIRouter, Query, status
from pydantic import BaseModel, ConfigDict, Field
from src.config import settings
from src.store.memory_store import memory_store

router = APIRouter(prefix="/mock", tags=["Developer Simulation & Testing"])


class SimulateInboundScheduleRequest(BaseModel):
    """Payload to simulate Alice sending a scheduling request."""
    model_config = ConfigDict(extra="allow")

    sender_e164: str = "+919876543210"
    sender_name: str = "Alice"
    text: str = "Remind Bob (+919123456789) tomorrow at 9:00 AM to review PR"
    phone_number_id: Optional[str] = None


class SimulateButtonClickRequest(BaseModel):
    """Payload to simulate an interactive button click."""
    model_config = ConfigDict(extra="allow")

    sender_e164: str = "+919876543210"
    button_id: str = "BTN_CONFIRM_SENT"
    button_title: str = "✅ I Sent It"
    phone_number_id: Optional[str] = None


class SimulateOptOutRequest(BaseModel):
    """Payload to simulate recipient opting out."""
    model_config = ConfigDict(extra="allow")

    sender_e164: str = "+919123456789"
    keyword: str = "STOP"
    phone_number_id: Optional[str] = None


class SimulateQualityUpdateRequest(BaseModel):
    """Payload to simulate Meta quality update event."""
    model_config = ConfigDict(extra="allow")

    phone_number_id: Optional[str] = None
    quality_rating: Literal["GREEN", "YELLOW", "RED"] = "YELLOW"
    event: Optional[str] = "ONGOING"


class SetQualityRequest(BaseModel):
    """Payload to directly set WABA phone quality."""
    model_config = ConfigDict(extra="allow")

    phone_number_id: Optional[str] = None
    quality_rating: Literal["GREEN", "YELLOW", "RED"] = "GREEN"


def _create_signed_webhook(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """Helper to generate json string and HMAC-SHA256 signature using compact JSON."""
    raw_bytes = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode("utf-8")
    sig = hmac.new(
        key=settings.APP_SECRET.encode("utf-8"),
        msg=raw_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return payload, f"sha256={sig}"





@router.post("/simulate/inbound-schedule", summary="Simulate Inbound User Schedule Message")
async def simulate_inbound_schedule(payload: SimulateInboundScheduleRequest) -> dict:
    """Constructs a signed Meta WhatsApp webhook payload for a user sending scheduling text."""
    phone_id = payload.phone_number_id or settings.DEFAULT_PHONE_NUMBER_ID
    clean_sender = payload.sender_e164.lstrip("+")
    msg_id = f"wamid.HBgL{uuid.uuid4().hex[:16]}"
    ts = str(int(time.time()))

    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": settings.WABA_ID,
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+16505551234",
                                "phone_number_id": phone_id,
                            },
                            "contacts": [
                                {
                                    "profile": {"name": payload.sender_name},
                                    "wa_id": clean_sender,
                                }
                            ],
                            "messages": [
                                {
                                    "from": clean_sender,
                                    "id": msg_id,
                                    "timestamp": ts,
                                    "type": "text",
                                    "text": {"body": payload.text},
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    formatted_payload, signature = _create_signed_webhook(webhook_data)
    memory_store.increment_metric("inbound_webhooks_total")

    return {
        "status": "simulated",
        "signature": signature,
        "payload": formatted_payload,
    }


@router.post("/simulate/button-click", summary="Simulate Interactive Button Click")
async def simulate_button_click(payload: SimulateButtonClickRequest) -> dict:
    """Constructs a signed Meta WhatsApp webhook payload for an interactive button reply."""
    phone_id = payload.phone_number_id or settings.DEFAULT_PHONE_NUMBER_ID
    clean_sender = payload.sender_e164.lstrip("+")
    msg_id = f"wamid.HBgL{uuid.uuid4().hex[:16]}"
    ts = str(int(time.time()))

    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": settings.WABA_ID,
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+16505551234",
                                "phone_number_id": phone_id,
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "User"},
                                    "wa_id": clean_sender,
                                }
                            ],
                            "messages": [
                                {
                                    "from": clean_sender,
                                    "id": msg_id,
                                    "timestamp": ts,
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {
                                            "id": payload.button_id,
                                            "title": payload.button_title,
                                        },
                                    },
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    formatted_payload, signature = _create_signed_webhook(webhook_data)
    memory_store.increment_metric("inbound_webhooks_total")

    return {
        "status": "simulated",
        "signature": signature,
        "payload": formatted_payload,
    }


@router.post("/simulate/opt-out", summary="Simulate User Opt-Out / STOP")
async def simulate_opt_out(payload: SimulateOptOutRequest) -> dict:
    """Simulates an inbound opt-out message (e.g., STOP or UNSUBSCRIBE) and increments metrics."""
    phone_id = payload.phone_number_id or settings.DEFAULT_PHONE_NUMBER_ID
    clean_sender = payload.sender_e164.lstrip("+")
    msg_id = f"wamid.HBgL{uuid.uuid4().hex[:16]}"
    ts = str(int(time.time()))

    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": settings.WABA_ID,
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "+16505551234",
                                "phone_number_id": phone_id,
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "OptOut User"},
                                    "wa_id": clean_sender,
                                }
                            ],
                            "messages": [
                                {
                                    "from": clean_sender,
                                    "id": msg_id,
                                    "timestamp": ts,
                                    "type": "text",
                                    "text": {"body": payload.keyword},
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    formatted_payload, signature = _create_signed_webhook(webhook_data)
    memory_store.increment_metric("inbound_webhooks_total")
    memory_store.increment_metric("opt_out_events_total")

    return {
        "status": "simulated_opt_out",
        "signature": signature,
        "payload": formatted_payload,
    }


@router.post("/simulate/quality-update", summary="Simulate WABA Quality Update Event")
async def simulate_quality_update(payload: SimulateQualityUpdateRequest) -> dict:
    """Simulates a Meta phone_number_quality_update event and updates state store."""
    phone_id = payload.phone_number_id or settings.DEFAULT_PHONE_NUMBER_ID

    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": settings.WABA_ID,
                "changes": [
                    {
                        "field": "phone_number_quality_update",
                        "value": {
                            "event": payload.event or "ONGOING",
                            "current_limit": "TIER_1K",
                            "phone_number": phone_id,
                            "quality_rating": payload.quality_rating,
                        },
                    }
                ],
            }
        ],
    }

    memory_store.set_quality_rating(phone_id, payload.quality_rating)
    memory_store.increment_metric("inbound_webhooks_total")

    formatted_payload, signature = _create_signed_webhook(webhook_data)
    return {
        "status": "simulated_quality_update",
        "phone_number_id": phone_id,
        "new_quality_rating": payload.quality_rating,
        "signature": signature,
        "payload": formatted_payload,
    }


@router.get("/outbox", summary="Inspect Dispatched Outbox Messages")
async def get_outbox(
    phone_number_id: Optional[str] = Query(None, description="Filter by phone_number_id"),
    recipient: Optional[str] = Query(None, description="Filter by recipient phone number"),
) -> dict:
    """Returns stored outbound messages sent to the mock Meta Graph API."""
    messages = memory_store.get_outbox(phone_number_id=phone_number_id, recipient=recipient)
    return {
        "total": len(messages),
        "messages": messages,
    }


@router.delete("/outbox", summary="Clear Dispatched Outbox Messages")
async def clear_outbox() -> dict:
    """Clears all dispatched messages from the mock outbox."""
    deleted_count = memory_store.clear_outbox()
    return {
        "status": "cleared",
        "deleted_count": deleted_count,
    }


@router.post("/set-quality", summary="Directly Set WABA Phone Quality Rating")
async def set_quality(payload: SetQualityRequest) -> dict:
    """Directly sets phone quality rating (GREEN, YELLOW, RED) in the state store."""
    phone_id = payload.phone_number_id or settings.DEFAULT_PHONE_NUMBER_ID
    memory_store.set_quality_rating(phone_id, payload.quality_rating)
    return {
        "phone_number_id": phone_id,
        "quality_rating": payload.quality_rating,
    }
