"""Pydantic v2 schemas for Meta WhatsApp Graph API v22.0."""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


class GraphLanguage(BaseModel):
    """Template language specification."""
    model_config = ConfigDict(extra="allow")

    code: str = "en"


class GraphParameter(BaseModel):
    """Component parameter."""
    model_config = ConfigDict(extra="allow")

    type: str = "text"
    text: Optional[str] = None
    payload: Optional[str] = None
    image: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None


class GraphComponent(BaseModel):
    """Template component (header, body, button)."""
    model_config = ConfigDict(extra="allow")

    type: Literal["header", "body", "button"]
    sub_type: Optional[str] = None
    index: Optional[str] = None
    parameters: Optional[List[GraphParameter]] = None


class GraphTemplate(BaseModel):
    """Template definition."""
    model_config = ConfigDict(extra="allow")

    name: str
    language: GraphLanguage = Field(default_factory=GraphLanguage)
    components: Optional[List[GraphComponent]] = None


class GraphInteractive(BaseModel):
    """Interactive message payload."""
    model_config = ConfigDict(extra="allow")

    type: str
    header: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, str]] = None
    footer: Optional[Dict[str, str]] = None
    action: Optional[Dict[str, Any]] = None


class GraphText(BaseModel):
    """Plain text message body."""
    model_config = ConfigDict(extra="allow")

    body: str
    preview_url: Optional[bool] = False


class GraphMessageSendRequest(BaseModel):
    """Outbound message request payload for POST /v22.0/{phone_number_id}/messages."""
    model_config = ConfigDict(extra="allow")

    messaging_product: str = "whatsapp"
    recipient_type: Optional[str] = "individual"
    to: str
    type: Literal["template", "interactive", "text"]
    template: Optional[GraphTemplate] = None
    interactive: Optional[GraphInteractive] = None
    text: Optional[GraphText] = None

    @model_validator(mode="after")
    def validate_type_payload(self) -> "GraphMessageSendRequest":
        if self.type == "template" and self.template is None:
            raise ValueError("Field 'template' is required when type is 'template'")
        if self.type == "interactive" and self.interactive is None:
            raise ValueError("Field 'interactive' is required when type is 'interactive'")
        if self.type == "text" and self.text is None:
            raise ValueError("Field 'text' is required when type is 'text'")
        return self


class GraphContactResponse(BaseModel):
    """Contact entry in Meta Graph response."""
    model_config = ConfigDict(extra="allow")

    input: str
    wa_id: str


class GraphMessageResponse(BaseModel):
    """Dispatched message reference containing wamid."""
    model_config = ConfigDict(extra="allow")

    id: str
    message_status: Optional[str] = "accepted"


class GraphMessageSendResponse(BaseModel):
    """Response returned by Meta Graph API v22.0 on successful message dispatch."""
    model_config = ConfigDict(extra="allow")

    messaging_product: str = "whatsapp"
    contacts: List[GraphContactResponse]
    messages: List[GraphMessageResponse]


class QualityRatingResponse(BaseModel):
    """Response for GET /v22.0/{phone_number_id}?fields=quality_rating."""
    model_config = ConfigDict(extra="allow")

    id: str
    quality_rating: Literal["GREEN", "YELLOW", "RED"]
