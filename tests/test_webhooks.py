"""Unit tests for Meta WhatsApp Inbound Webhooks."""
import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from src.app import create_app
from src.config import settings
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


def test_webhook_handshake_success(client):
    """Test successful GET /webhooks/whatsapp handshake."""
    challenge = "1158201444"
    response = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.WEBHOOK_VERIFY_TOKEN,
            "hub.challenge": challenge,
        },
    )
    assert response.status_code == 200
    assert response.text == challenge


def test_webhook_handshake_invalid_token(client):
    """Test GET /webhooks/whatsapp with invalid verify token."""
    response = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 403
    assert "mismatch" in response.json()["detail"].lower()


def test_webhook_handshake_invalid_mode(client):
    """Test GET /webhooks/whatsapp with invalid hub.mode."""
    response = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "unsubscribe",
            "hub.verify_token": settings.WEBHOOK_VERIFY_TOKEN,
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 403


def test_webhook_post_without_signature(client):
    """Test POST /webhooks/whatsapp accepts valid json payload without signature header."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": settings.WABA_ID,
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "phone_number_id": settings.DEFAULT_PHONE_NUMBER_ID
                            },
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.HBgL12345",
                                    "timestamp": "1700000000",
                                    "type": "text",
                                    "text": {"body": "Hello bot"},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }
    response = client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "EVENT_RECEIVED", "success": True}
    assert memory_store.get_metric("inbound_webhooks_total") == 1


def test_webhook_post_with_valid_hmac(client):
    """Test POST /webhooks/whatsapp with valid X-Hub-Signature-256 header."""
    payload = {"object": "whatsapp_business_account", "entry": []}
    raw_bytes = json.dumps(payload).encode("utf-8")
    sig = hmac.new(settings.APP_SECRET.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()

    response = client.post(
        "/webhooks/whatsapp",
        content=raw_bytes,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": f"sha256={sig}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "EVENT_RECEIVED"


def test_webhook_post_with_invalid_hmac(client):
    """Test POST /webhooks/whatsapp rejects payload with forged signature."""
    payload = {"object": "whatsapp_business_account", "entry": []}
    raw_bytes = json.dumps(payload).encode("utf-8")

    response = client.post(
        "/webhooks/whatsapp",
        content=raw_bytes,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=forged_hex_signature"},
    )
    assert response.status_code == 403
    assert "verification failed" in response.json()["detail"].lower()


def test_webhook_malformed_signature_header(client):
    """Test POST /webhooks/whatsapp rejects signature not starting with sha256=."""
    response = client.post(
        "/webhooks/whatsapp",
        content=b"{}",
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": "md5=123456"},
    )
    assert response.status_code == 403
    assert "format" in response.json()["detail"].lower()



def test_webhook_quality_update_event(client):
    """Test that phone_number_quality_update event modifies state store rating."""
    phone_id = "test_phone_id_999"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": settings.WABA_ID,
                "changes": [
                    {
                        "field": "phone_number_quality_update",
                        "value": {
                            "phone_number": phone_id,
                            "quality_rating": "YELLOW",
                        },
                    }
                ],
            }
        ],
    }
    response = client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    assert memory_store.get_quality_rating(phone_id) == "YELLOW"


def test_webhook_opt_out_keyword_event(client):
    """Test that messages containing STOP increment opt_out_events_total."""
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": settings.WABA_ID,
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": settings.DEFAULT_PHONE_NUMBER_ID},
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.STOP123",
                                    "timestamp": "1700000000",
                                    "type": "text",
                                    "text": {"body": "STOP"},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }
    response = client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    assert memory_store.get_metric("opt_out_events_total") == 1


def test_webhook_malformed_json_list_payload(client):
    """Test that webhook handles non-dict JSON root (e.g. list) gracefully without 500 error."""
    response = client.post(
        "/webhooks/whatsapp",
        content=b"[]",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "EVENT_RECEIVED", "success": True}


def test_webhook_malformed_entries_and_changes(client):
    """Test that non-dict entries and malformed changes are safely skipped."""
    payload = {
        "entry": [
            "invalid_string_entry",
            12345,
            {"changes": "invalid_changes_type"},
            {"changes": [None, 999, {"field": "messages", "value": "not_a_dict"}]},
            {"changes": [{"field": "messages", "value": {"messages": "not_a_list"}}]},
            {
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messages": [
                                "not_a_dict_msg",
                                {"type": "text", "text": "not_a_dict_text"},
                                {"type": "interactive", "interactive": "not_a_dict_interactive"},
                            ]
                        },
                    }
                ]
            },
        ]
    }
    response = client.post("/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "EVENT_RECEIVED", "success": True}
