"""Unit tests for Observability and Telemetry endpoints."""
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


def test_health_check(client):
    """Test GET /health liveness probe."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "version" in data
    assert data["service"] == "MockAPI_Server"


def test_metrics_prometheus_exposition(client):
    """Test GET /metrics returns standard Prometheus formatted telemetry."""
    # Generate some metrics
    memory_store.increment_metric("inbound_webhooks_total", 3)
    memory_store.increment_metric("outbound_messages_total", 2)
    memory_store.increment_metric("opt_out_events_total", 1)

    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text

    assert "# HELP waba_quality_rating" in body
    assert "# TYPE waba_quality_rating gauge" in body
    assert "inbound_webhooks_total 3" in body
    assert "outbound_messages_total 2" in body
    assert "opt_out_events_total 1" in body


def test_root_index(client):
    """Test GET / root landing response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["docs"] == "/docs"


def test_modal_app_entrypoint():
    """Test that modal_app exports an active FastAPI app via ASGI entrypoint."""
    import modal_app
    app_instance = modal_app.fastapi_app.local()
    assert app_instance is not None
    assert app_instance.title == "SchedulerBot v4.4 Mock API Server"


