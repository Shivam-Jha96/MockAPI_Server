"""Observability routes for health checking and Prometheus metrics."""
from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from src.config import settings
from src.store.memory_store import memory_store

router = APIRouter(tags=["Observability"])


@router.get("/health", summary="Container Health & Liveness Probe")
async def health_check() -> dict:
    """Returns application health status and current timestamp."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME,
    }


@router.get("/metrics", summary="Prometheus Telemetry Metrics")
async def get_metrics() -> Response:
    """Returns Prometheus exposition formatted operational metrics."""
    metrics_text = memory_store.get_metrics_prometheus(default_phone_id=settings.DEFAULT_PHONE_NUMBER_ID)
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8",
        status_code=status.HTTP_200_OK,
    )
