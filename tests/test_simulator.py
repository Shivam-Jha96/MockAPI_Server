"""Unit tests for Developer Simulator and Testing endpoints."""
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


def test_simulate_inbound_schedule(client):
    """Test simulation of Alice sending an inbound schedule text."""
    payload = {
        "sender_e164": "+919876543210",
        "sender_name": "Alice",
        "text": "Remind Bob (+919123456789) tomorrow at 9:00 AM",
    }
    response = client.post("/mock/simulate/inbound-schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "simulated"
    assert data["signature"].startswith("sha256=")
    assert data["payload"]["object"] == "whatsapp_business_account"
    assert memory_store.get_metric("inbound_webhooks_total") == 1


def test_simulate_button_click(client):
    """Test simulation of interactive button reply click."""
    payload = {
        "sender_e164": "+919876543210",
        "button_id": "BTN_CONFIRM_SENT",
        "button_title": "✅ I Sent It",
    }
    response = client.post("/mock/simulate/button-click", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "simulated"
    assert data["signature"].startswith("sha256=")
    messages = data["payload"]["entry"][0]["changes"][0]["value"]["messages"]
    assert messages[0]["interactive"]["button_reply"]["id"] == "BTN_CONFIRM_SENT"


def test_simulate_opt_out(client):
    """Test simulation of user sending STOP opt-out."""
    payload = {
        "sender_e164": "+919123456789",
        "keyword": "STOP",
    }
    response = client.post("/mock/simulate/opt-out", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "simulated_opt_out"
    assert memory_store.get_metric("opt_out_events_total") == 1


def test_simulate_quality_update(client):
    """Test simulation of Meta WABA quality downgrade."""
    payload = {
        "phone_number_id": "phone_sim_123",
        "quality_rating": "YELLOW",
    }
    response = client.post("/mock/simulate/quality-update", json=payload)
    assert response.status_code == 200
    assert response.json()["new_quality_rating"] == "YELLOW"
    assert memory_store.get_quality_rating("phone_sim_123") == "YELLOW"


def test_outbox_inspection_and_clear(client):
    """Test outbox message tracking, filtering, and clearing."""
    phone_id = "phone_outbox_test"
    # Send two messages
    client.post(
        f"/v22.0/{phone_id}/messages",
        json={"to": "+919111111111", "type": "text", "text": {"body": "Msg 1"}},
    )
    client.post(
        f"/v22.0/{phone_id}/messages",
        json={"to": "+919222222222", "type": "text", "text": {"body": "Msg 2"}},
    )

    # Inspect all
    res_all = client.get("/mock/outbox")
    assert res_all.status_code == 200
    assert res_all.json()["total"] == 2

    # Filter by recipient
    res_filtered = client.get("/mock/outbox", params={"recipient": "+919111111111"})
    assert res_filtered.json()["total"] == 1
    assert res_filtered.json()["messages"][0]["to"] == "+919111111111"

    # Delete outbox
    res_del = client.delete("/mock/outbox")
    assert res_del.status_code == 200
    assert res_del.json()["deleted_count"] == 2

    # Verify outbox is empty
    assert client.get("/mock/outbox").json()["total"] == 0


def test_set_quality_direct(client):
    """Test setting quality directly via /mock/set-quality."""
    phone_id = "direct_quality_phone"
    res = client.post("/mock/set-quality", json={"phone_number_id": phone_id, "quality_rating": "RED"})
    assert res.status_code == 200
    assert memory_store.get_quality_rating(phone_id) == "RED"


def test_simulator_to_webhook_signed_delivery_roundtrip(client):
    """Test that simulated signed webhook payload passes live verification on /webhooks/whatsapp."""
    sim_res = client.post(
        "/mock/simulate/inbound-schedule",
        json={
            "sender_e164": "+919876543210",
            "sender_name": "Alice",
            "text": "Remind Bob (+919123456789) tomorrow at 9:00 AM to review PR",
        },
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    signature = sim_data["signature"]
    payload = sim_data["payload"]

    # Forward payload to webhook endpoint using standard HTTP client json formatting
    webhook_res = client.post(
        "/webhooks/whatsapp",
        json=payload,
        headers={"X-Hub-Signature-256": signature},
    )
    assert webhook_res.status_code == 200
    assert webhook_res.json() == {"status": "EVENT_RECEIVED", "success": True}


def test_simulator_button_click_emoji_webhook_roundtrip(client):
    """Test that simulated button click with default and custom emojis correctly delivers to /webhooks/whatsapp."""
    # 1. Test default button click with "✅ I Sent It"
    default_sim_res = client.post("/mock/simulate/button-click", json={})
    assert default_sim_res.status_code == 200
    default_data = default_sim_res.json()
    assert default_data["status"] == "simulated"
    default_payload = default_data["payload"]
    default_signature = default_data["signature"]

    webhook_res_default = client.post(
        "/webhooks/whatsapp",
        json=default_payload,
        headers={"X-Hub-Signature-256": default_signature},
    )
    assert webhook_res_default.status_code == 200
    assert webhook_res_default.json() == {"status": "EVENT_RECEIVED", "success": True}

    # 2. Test button click with custom emojis
    custom_cases = [
        {"button_id": "BTN_SEND_BOT", "button_title": "🤖 Send via Bot Now"},
        {"button_id": "BTN_CANCEL", "button_title": "❌ Cancel Schedule"},
        {"button_id": "BTN_CUSTOM_CELEBRATE", "button_title": "🎉 Multilingual & Emojis 🚀✨"},
    ]
    for case in custom_cases:
        sim_res = client.post(
            "/mock/simulate/button-click",
            json={
                "sender_e164": "+919876543210",
                "button_id": case["button_id"],
                "button_title": case["button_title"],
            },
        )
        assert sim_res.status_code == 200
        sim_data = sim_res.json()
        payload = sim_data["payload"]
        signature = sim_data["signature"]

        webhook_res = client.post(
            "/webhooks/whatsapp",
            json=payload,
            headers={"X-Hub-Signature-256": signature},
        )
        assert webhook_res.status_code == 200
        assert webhook_res.json() == {"status": "EVENT_RECEIVED", "success": True}


def test_memory_store_outbox_bounding():
    """Test that outbox respects maxlen bounding and prevents unbounded memory growth."""
    store = memory_store
    store.clear_outbox()

    # Add 1050 messages
    for i in range(1050):
        store.add_outbox_message({"to": f"+91900000{i:04d}", "type": "text", "body": f"msg_{i}"})

    outbox = store.get_outbox()
    assert len(outbox) == 1000
    # Oldest 50 messages should be pruned
    assert outbox[0]["to"] == "+919000000050"
    assert outbox[-1]["to"] == "+919000001049"
