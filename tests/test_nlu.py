"""Unit tests for NLU Schedule Parsing Service."""
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


def test_parse_complete_schedule(client):
    """Test parsing complete scheduling instruction."""
    payload = {
        "raw_text": "Remind Bob (+919123456789) tomorrow at 9:00 AM saying 'Please submit the monthly report'",
        "current_time": "2026-11-21T10:00:00Z",
    }
    response = client.post("/v1/parse-schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "SCHEDULE_RELAY"
    assert data["recipient_name"] == "Bob"
    assert data["recipient_e164"] == "+919123456789"
    assert "2026-11-22T09:00:00" in data["scheduled_at_iso"]
    assert "Please submit the monthly report" in data["message_body"]
    assert data["validation"]["is_valid"] is True
    assert len(data["validation"]["missing_fields"]) == 0


def test_parse_relative_time(client):
    """Test parsing relative time offset (in 2 hours)."""
    payload = {
        "raw_text": "Send to Charlie (+14155552671) in 2 hours with body: Don't forget our sync call",
        "current_time": "2026-11-21T10:00:00Z",
    }
    response = client.post("/v1/parse-schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "SCHEDULE_RELAY"
    assert data["recipient_name"] == "Charlie"
    assert data["recipient_e164"] == "+14155552671"
    assert "2026-11-21T12:00:00" in data["scheduled_at_iso"]
    assert "Don't forget our sync call" in data["message_body"]
    assert data["validation"]["is_valid"] is True


def test_parse_cancel_schedule(client):
    """Test intent classification for cancellation."""
    payload = {"raw_text": "Cancel schedule for Bob"}
    response = client.post("/v1/parse-schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "CANCEL_SCHEDULE"
    assert data["validation"]["is_valid"] is True


def test_parse_opt_out(client):
    """Test intent classification for STOP / UNSUBSCRIBE."""
    payload = {"raw_text": "STOP"}
    response = client.post("/v1/parse-schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "OPT_OUT"
    assert data["validation"]["is_valid"] is True


def test_parse_incomplete_schedule(client):
    """Test validation failure on missing time or recipient phone."""
    payload = {"raw_text": "Remind someone to review PR"}
    response = client.post("/v1/parse-schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["validation"]["is_valid"] is False
    assert "recipient_e164" in data["validation"]["missing_fields"]
    assert "scheduled_at_iso" in data["validation"]["missing_fields"]


def test_parse_formatted_international_phone_numbers(client):
    """Test parsing formatted phone numbers with spaces, hyphens, and area codes."""
    # Hyphenated US format
    payload1 = {
        "raw_text": "Remind Alice (+1-415-555-0199) tomorrow at 9:00 AM saying 'Check deployment'",
        "current_time": "2026-11-21T10:00:00Z",
    }
    res1 = client.post("/v1/parse-schedule", json=payload1)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["recipient_name"] == "Alice"
    assert data1["recipient_e164"] == "+14155550199"
    assert data1["validation"]["is_valid"] is True

    # Spaced UK format
    payload2 = {
        "raw_text": "Remind David (+44 7911 123456) in 1 hour saying 'London meeting'",
        "current_time": "2026-11-21T10:00:00Z",
    }
    res2 = client.post("/v1/parse-schedule", json=payload2)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["recipient_name"] == "David"
    assert data2["recipient_e164"] == "+447911123456"
    assert data2["validation"]["is_valid"] is True

    # Standalone formatted phone without parentheses
    payload3 = {
        "raw_text": "Send to +1-415-555-0199 in 30 minutes with body: Direct reminder",
        "current_time": "2026-11-21T10:00:00Z",
    }
    res3 = client.post("/v1/parse-schedule", json=payload3)
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["recipient_e164"] == "+14155550199"
    assert data3["validation"]["is_valid"] is True


def test_parse_invalid_time_bounds_graceful_handling(client):
    """Test that out-of-bounds time strings do not crash with 500 and return is_valid=False."""
    # Out-of-bounds hour & minute (25:99)
    res1 = client.post(
        "/v1/parse-schedule",
        json={"raw_text": "Remind Bob (+919123456789) at 25:99 saying 'Invalid time'"},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["validation"]["is_valid"] is False
    assert "scheduled_at_iso" in data1["validation"]["missing_fields"]

    # Address mistaken for time ("tomorrow at 99 Park Ave")
    res2 = client.post(
        "/v1/parse-schedule",
        json={"raw_text": "Remind Bob (+919123456789) tomorrow at 99 Park Ave saying 'Meet at office'"},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["validation"]["is_valid"] is False
    assert "scheduled_at_iso" in data2["validation"]["missing_fields"]

    # Huge integer causing timedelta OverflowError
    res3 = client.post(
        "/v1/parse-schedule",
        json={"raw_text": "Remind Bob (+919123456789) in 99999999999999999 hours saying 'Overflow test'"},
    )
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["validation"]["is_valid"] is False
    assert "scheduled_at_iso" in data3["validation"]["missing_fields"]
