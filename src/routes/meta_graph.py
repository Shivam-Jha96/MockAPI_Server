"""Mock Meta WhatsApp Graph API v22.0 routes."""
import uuid
from typing import Optional
from fastapi import APIRouter, Path, Query, status
from src.schemas.meta_graph import (
    GraphMessageSendRequest,
    GraphMessageSendResponse,
    GraphContactResponse,
    GraphMessageResponse,
    QualityRatingResponse,
)
from src.store.memory_store import memory_store

router = APIRouter(prefix="/v22.0", tags=["Meta WhatsApp Graph API v22.0"])


@router.post(
    "/{phone_number_id}/messages",
    response_model=GraphMessageSendResponse,
    status_code=status.HTTP_200_OK,
    summary="Send WhatsApp Outbound Message (Templates, Interactive, Text)",
)
async def send_message(
    payload: GraphMessageSendRequest,
    phone_number_id: str = Path(..., description="Meta Phone Number ID"),
) -> GraphMessageSendResponse:
    """Simulates Meta WhatsApp Graph API v22.0 message dispatch."""
    clean_wa_id = payload.to.lstrip("+")
    wamid = f"wamid.HBgL{uuid.uuid4().hex[:20].upper()}"

    outbox_record = {
        "phone_number_id": phone_number_id,
        "to": payload.to,
        "recipient_type": payload.recipient_type,
        "type": payload.type,
        "template": payload.template.model_dump() if payload.template else None,
        "interactive": payload.interactive.model_dump() if payload.interactive else None,
        "text": payload.text.model_dump() if payload.text else None,
        "wamid": wamid,
        "status": "accepted",
    }
    memory_store.add_outbox_message(outbox_record)

    return GraphMessageSendResponse(
        messaging_product="whatsapp",
        contacts=[GraphContactResponse(input=payload.to, wa_id=clean_wa_id)],
        messages=[GraphMessageResponse(id=wamid, message_status="accepted")],
    )


@router.get(
    "/{phone_number_id}",
    response_model=QualityRatingResponse,
    summary="Query WhatsApp Business Account Quality Rating",
)
async def get_phone_quality(
    phone_number_id: str = Path(..., description="Meta Phone Number ID"),
    fields: Optional[str] = Query(None, description="Comma-separated fields, e.g. 'quality_rating'"),
) -> QualityRatingResponse:
    """Returns the current quality status (GREEN, YELLOW, RED) of the phone number."""
    rating = memory_store.get_quality_rating(phone_number_id)
    return QualityRatingResponse(id=phone_number_id, quality_rating=rating)  # type: ignore[arg-type]
