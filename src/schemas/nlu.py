"""Pydantic v2 schemas for NLU Natural Language Schedule parsing."""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class ParseScheduleRequest(BaseModel):
    """Request payload for POST /v1/parse-schedule."""
    model_config = ConfigDict(extra="allow")

    raw_text: str
    sender_e164: Optional[str] = None
    timezone: Optional[str] = "Asia/Kolkata"
    current_time: Optional[str] = None


class ValidationResult(BaseModel):
    """Validation status of parsed scheduling instruction."""
    model_config = ConfigDict(extra="allow")

    is_valid: bool
    missing_fields: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ParseScheduleResponse(BaseModel):
    """Structured extraction response from NLU parser."""
    model_config = ConfigDict(extra="allow")

    intent: Literal["SCHEDULE_RELAY", "CANCEL_SCHEDULE", "OPT_OUT", "UNKNOWN"]
    recipient_name: Optional[str] = None
    recipient_e164: Optional[str] = None
    scheduled_at_iso: Optional[str] = None
    message_body: Optional[str] = None
    confidence: float = 0.95
    validation: ValidationResult
