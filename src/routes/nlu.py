"""Mock NLU / LLM Schedule Parsing Service."""
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List
from fastapi import APIRouter, status
from src.schemas.nlu import (
    ParseScheduleRequest,
    ParseScheduleResponse,
    ValidationResult,
)
from src.store.memory_store import memory_store

router = APIRouter(prefix="/v1", tags=["NLU Schedule Parser"])


def _extract_intent(text: str) -> str:
    """Classify user intent based on text tokens."""
    lower = text.lower()
    if any(k in lower for k in ("stop", "unsubscribe", "opt out", "opt-out")):
        return "OPT_OUT"
    if any(k in lower for k in ("cancel", "abort", "delete schedule", "revoke")):
        return "CANCEL_SCHEDULE"
    if any(k in lower for k in ("remind", "schedule", "send", "notify", "ping", "message")):
        return "SCHEDULE_RELAY"
    return "UNKNOWN"


def _normalize_phone(raw_phone: str) -> Optional[str]:
    """Extract clean digits and return in E.164 format (+<digits>) if valid length."""
    digits = re.sub(r'\D', '', raw_phone)
    if 10 <= len(digits) <= 15:
        return f"+{digits}"
    return None


def _extract_recipient(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract recipient name and E.164 phone number."""
    # Pattern 1: Name and phone in parentheses e.g. "Bob (+919876543210)", "Alice (+1-415-555-0199)"
    m_paren = re.search(r'([A-Z][a-z]+)\s*\(\s*([+\d\s\-()]{9,25})\s*\)', text)
    if m_paren:
        name = m_paren.group(1)
        phone = _normalize_phone(m_paren.group(2))
        if phone:
            return name, phone

    # Pattern 2: Formatted or unformatted E.164 phone number anywhere
    # Handles e.g. +1-415-555-0199, +44 7911 123456, +919123456789
    phone = None
    for m in re.finditer(r'(\+[\d\s\-]{8,22}\d|\b\d[\d\s\-]{8,18}\d\b)', text):
        candidate = _normalize_phone(m.group(1))
        if candidate:
            phone = candidate
            break

    # Extract name near "to", "remind", "tell"
    m_name = re.search(r'(?:remind|to|tell|send to)\s+([A-Z][a-z]+)', text, re.IGNORECASE)
    name = m_name.group(1) if m_name else None

    return name, phone


def _extract_scheduled_time(text: str, base_time: datetime) -> Optional[str]:
    """Parse relative or absolute time phrases into ISO 8601 string."""
    try:
        lower = text.lower()

        # In X hours / minutes
        m_in_hours = re.search(r'in\s+(\d+)\s*(?:hours|hour|hrs|hr)', lower)
        if m_in_hours:
            hrs = int(m_in_hours.group(1))
            dt = base_time + timedelta(hours=hrs)
            return dt.isoformat()

        m_in_mins = re.search(r'in\s+(\d+)\s*(?:minutes|minute|mins|min)', lower)
        if m_in_mins:
            mins = int(m_in_mins.group(1))
            dt = base_time + timedelta(minutes=mins)
            return dt.isoformat()

        # Tomorrow / Today at HH:MM AM/PM
        is_tomorrow = "tomorrow" in lower
        is_today = "today" in lower

        for m_time in re.finditer(r'(?:at|by)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', lower):
            hour = int(m_time.group(1))
            minute = int(m_time.group(2) or 0)
            meridiem = m_time.group(3)

            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0

            # Validate bounds before datetime replace
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                continue

            target_date = base_time.date()
            if is_tomorrow:
                target_date += timedelta(days=1)

            dt = base_time.replace(
                year=target_date.year,
                month=target_date.month,
                day=target_date.day,
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )
            return dt.isoformat()

        # Direct ISO 8601 regex pattern
        m_iso = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', text)
        if m_iso:
            return m_iso.group(0)

        return None
    except (ValueError, OverflowError):
        return None


def _extract_message_body(text: str) -> Optional[str]:
    """Extract intended message body from natural language scheduling prompt."""
    # Look for quotes: '...' or "..."
    m_quote = re.search(r'["\']([^"\']+)["\']', text)
    if m_quote:
        return m_quote.group(1).strip()

    # Look for keywords: "saying", "message:", "that:", "body:"
    m_kw = re.search(r'(?:saying|message:|body:|that|with text:?)\s+(.+)$', text, re.IGNORECASE)
    if m_kw:
        return m_kw.group(1).strip()

    # Look for "to <action/body>" at the end
    m_to = re.search(r'(?:to)\s+([a-zA-Z0-9\s,\.!\?]+)$', text, re.IGNORECASE)
    if m_to:
        candidate = m_to.group(1).strip()
        # Avoid returning just a recipient name
        if len(candidate.split()) > 1:
            return candidate

    return None


@router.post(
    "/parse-schedule",
    response_model=ParseScheduleResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse Natural Language Scheduling Request",
)
async def parse_schedule(payload: ParseScheduleRequest) -> ParseScheduleResponse:
    """Mock NLU extraction service that extracts recipient, timestamp, and message body."""
    memory_store.increment_metric("parse_schedule_requests_total")

    raw_text = payload.raw_text.strip()
    intent = _extract_intent(raw_text)

    # Reference time
    if payload.current_time:
        try:
            base_time = datetime.fromisoformat(payload.current_time.replace("Z", "+00:00"))
        except Exception:
            base_time = datetime.now(timezone.utc)
    else:
        base_time = datetime.now(timezone.utc)

    if intent in ("OPT_OUT", "CANCEL_SCHEDULE"):
        return ParseScheduleResponse(
            intent=intent,
            recipient_name=None,
            recipient_e164=None,
            scheduled_at_iso=None,
            message_body=None,
            confidence=0.98,
            validation=ValidationResult(is_valid=True, missing_fields=[], errors=[]),
        )

    name, phone = _extract_recipient(raw_text)
    scheduled_at = _extract_scheduled_time(raw_text, base_time)
    message_body = _extract_message_body(raw_text)

    # Validation
    missing: List[str] = []
    errors: List[str] = []

    if not phone:
        missing.append("recipient_e164")
    if not scheduled_at:
        missing.append("scheduled_at_iso")
    if not message_body:
        missing.append("message_body")

    if missing:
        errors.append(f"Missing required scheduling parameters: {', '.join(missing)}")
        is_valid = False
    else:
        is_valid = True

    confidence = 0.95 if is_valid else 0.50

    return ParseScheduleResponse(
        intent="SCHEDULE_RELAY" if (is_valid or phone or scheduled_at) else "UNKNOWN",
        recipient_name=name,
        recipient_e164=phone,
        scheduled_at_iso=scheduled_at,
        message_body=message_body,
        confidence=confidence,
        validation=ValidationResult(
            is_valid=is_valid,
            missing_fields=missing,
            errors=errors,
        ),
    )
