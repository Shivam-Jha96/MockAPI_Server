"""Unit tests for Meta WhatsApp Graph API v22.0 endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.app import create_app
from src.store.memory_store import memory_store


@pytest.fixture(autouse=True)
def reset_store():
    """Reset store before each test."""
    memory_store.reset()
    yield
    memory_store.reset()


@pytest.fixture
def client():
    """Test client fixture."""
    app = create_app()
    return TestClient(app)


def test_send_template_message(client):
    """Test POST /v22.0/{phone_number_id}/messages with template."""
    phone_id = "109876543210987"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "+919876543210",
        "type": "template",
        "template": {
            "name": "hybrid_notify_alice_v1",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": "Bob"},
                        {"type": "text", "text": "tomorrow at 9:00 AM"},
                    ],
                }
            ],
        },
    }
    response = client.post(f"/v22.0/{phone_id}/messages", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["messaging_product"] == "whatsapp"
    assert len(data["contacts"]) == 1
    assert data["contacts"][0]["input"] == "+919876543210"
    assert data["contacts"][0]["wa_id"] == "919876543210"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["id"].startswith("wamid.HBgL")

    # Check that outbox captured it
    outbox = memory_store.get_outbox(phone_number_id=phone_id)
    assert len(outbox) == 1
    assert outbox[0]["to"] == "+919876543210"
    assert outbox[0]["template"]["name"] == "hybrid_notify_alice_v1"


def test_send_interactive_message(client):
    """Test POST /v22.0/{phone_number_id}/messages with interactive buttons."""
    phone_id = "109876543210987"
    payload = {
        "messaging_product": "whatsapp",
        "to": "+919876543210",
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Choose an action for your scheduled message:"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "BTN_CONFIRM_SENT", "title": "✅ I Sent It"}},
                    {"type": "reply", "reply": {"id": "BTN_RELAY_BOT", "title": "🤖 Send via Bot Now"}},
                    {"type": "reply", "reply": {"id": "BTN_CANCEL", "title": "❌ Cancel Schedule"}},
                ]
            },
        },
    }
    response = client.post(f"/v22.0/{phone_id}/messages", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 1
    assert data["messages"][0]["id"].startswith("wamid.HBgL")

    outbox = memory_store.get_outbox(recipient="+919876543210")
    assert len(outbox) == 1
    assert outbox[0]["type"] == "interactive"


def test_send_text_message(client):
    """Test POST /v22.0/{phone_number_id}/messages with session text."""
    phone_id = "109876543210987"
    payload = {
        "messaging_product": "whatsapp",
        "to": "+919876543210",
        "type": "text",
        "text": {"body": "This is a direct text message."},
    }
    response = client.post(f"/v22.0/{phone_id}/messages", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 1

    outbox = memory_store.get_outbox()
    assert len(outbox) == 1
    assert outbox[0]["text"]["body"] == "This is a direct text message."


def test_get_quality_rating(client):
    """Test GET /v22.0/{phone_number_id}?fields=quality_rating."""
    phone_id = "109876543210987"
    # Defaults to GREEN
    res1 = client.get(f"/v22.0/{phone_id}?fields=quality_rating")
    assert res1.status_code == 200
    assert res1.json() == {"id": phone_id, "quality_rating": "GREEN"}

    # Update in store and verify
    memory_store.set_quality_rating(phone_id, "RED")
    res2 = client.get(f"/v22.0/{phone_id}?fields=quality_rating")
    assert res2.status_code == 200
    assert res2.json() == {"id": phone_id, "quality_rating": "RED"}


def test_graph_message_request_validation_missing_type_payloads(client):
    """Test that GraphMessageSendRequest validator rejects requests missing corresponding type payload."""
    phone_id = "109876543210987"

    # Template type without template field
    res_template = client.post(
        f"/v22.0/{phone_id}/messages",
        json={"to": "+919876543210", "type": "template"},
    )
    assert res_template.status_code == 422
    assert "template" in str(res_template.json()).lower()

    # Interactive type without interactive field
    res_interactive = client.post(
        f"/v22.0/{phone_id}/messages",
        json={"to": "+919876543210", "type": "interactive"},
    )
    assert res_interactive.status_code == 422
    assert "interactive" in str(res_interactive.json()).lower()

    # Text type without text field
    res_text = client.post(
        f"/v22.0/{phone_id}/messages",
        json={"to": "+919876543210", "type": "text"},
    )
    assert res_text.status_code == 422
    assert "text" in str(res_text.json()).lower()
