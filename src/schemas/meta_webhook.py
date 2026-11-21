"""Pydantic v2 schemas for Meta WhatsApp Inbound Webhooks."""
from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, ConfigDict


class WebhookChallengeParams(BaseModel):
    """Query parameters for Meta Webhook verification handshake."""
    model_config = ConfigDict(populate_by_name=True)

    hub_mode: str = Field(alias="hub.mode")
    hub_challenge: str = Field(alias="hub.challenge")
    hub_verify_token: str = Field(alias="hub.verify_token")


class WebhookTextMessage(BaseModel):
    """Text body of incoming message."""
    model_config = ConfigDict(extra="allow")

    body: str


class WebhookButtonReply(BaseModel):
    """Button reply details."""
    model_config = ConfigDict(extra="allow")

    id: str
    title: str


class WebhookInteractiveMessage(BaseModel):
    """Interactive message payload (e.g., button reply)."""
    model_config = ConfigDict(extra="allow")

    type: Literal["button_reply", "list_reply"]
    button_reply: Optional[WebhookButtonReply] = None


class WebhookInboundMessage(BaseModel):
    """Single inbound message item."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    from_user: str = Field(alias="from")
    id: str
    timestamp: str
    type: str = "text"
    text: Optional[WebhookTextMessage] = None
    interactive: Optional[WebhookInteractiveMessage] = None


class WebhookStatus(BaseModel):
    """Delivery status update item."""
    model_config = ConfigDict(extra="allow")

    id: str
    status: Literal["sent", "delivered", "read", "failed"]
    timestamp: str
    recipient_id: str
    conversation: Optional[Dict[str, Any]] = None
    pricing: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None


class WebhookProfile(BaseModel):
    """User profile information."""
    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None


class WebhookContact(BaseModel):
    """Contact entry."""
    model_config = ConfigDict(extra="allow")

    profile: Optional[WebhookProfile] = None
    wa_id: str


class WebhookMetadata(BaseModel):
    """Metadata regarding the receiving WABA phone number."""
    model_config = ConfigDict(extra="allow")

    display_phone_number: Optional[str] = None
    phone_number_id: Optional[str] = None


class WebhookValueMessages(BaseModel):
    """Value object for messages field change."""
    model_config = ConfigDict(extra="allow")

    messaging_product: str = "whatsapp"
    metadata: WebhookMetadata
    contacts: Optional[List[WebhookContact]] = None
    messages: Optional[List[WebhookInboundMessage]] = None
    statuses: Optional[List[WebhookStatus]] = None


class WebhookValueQuality(BaseModel):
    """Value object for phone_number_quality_update field change."""
    model_config = ConfigDict(extra="allow")

    event: Optional[str] = None
    current_limit: Optional[str] = None
    phone_number: Optional[str] = None
    quality_rating: Optional[Literal["GREEN", "YELLOW", "RED"]] = None


class WebhookChange(BaseModel):
    """Single change event item."""
    model_config = ConfigDict(extra="allow")

    field: str
    value: Union[WebhookValueMessages, WebhookValueQuality, Dict[str, Any]]


class WebhookEntry(BaseModel):
    """Entry containing changes."""
    model_config = ConfigDict(extra="allow")

    id: str
    changes: List[WebhookChange]


class WebhookPayload(BaseModel):
    """Master Webhook Payload received from Meta."""
    model_config = ConfigDict(extra="allow")

    object: str = "whatsapp_business_account"
    entry: List[WebhookEntry]
