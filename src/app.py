"""FastAPI Application factory for SchedulerBot v4.4 Mock API Server."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes.webhooks import router as webhooks_router
from src.routes.meta_graph import router as meta_graph_router
from src.routes.nlu import router as nlu_router
from src.routes.kms import router as kms_router
from src.routes.observability import router as observability_router
from src.routes.simulator import router as simulator_router


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application instance."""
    app = FastAPI(
        title="SchedulerBot v4.4 Mock API Server",
        description=(
            "Production-grade Mock API Server conforming to the SchedulerBot v4.4 Specification.\n\n"
            "Features:\n"
            "- Meta WhatsApp Business Graph API v22.0 (Templates, Interactive, Session Text, Quality Queries)\n"
            "- Inbound Webhooks Handshake & Event Ingestion (HMAC-SHA256 signature verification)\n"
            "- NLU / LLM Schedule Parsing Service\n"
            "- Cloud KMS Mock Cryptographic Operations (AES-256-GCM)\n"
            "- Developer Simulation Harness & Outbox Inspection\n"
            "- Prometheus Telemetry & Health Observability"
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Enable CORS for local testing and developer tooling
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include all route modules
    app.include_router(observability_router)
    app.include_router(webhooks_router)
    app.include_router(meta_graph_router)
    app.include_router(nlu_router)
    app.include_router(kms_router)
    app.include_router(simulator_router)

    @app.get("/", tags=["Root"])
    async def root_index() -> dict:
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "online",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "metrics": "/metrics",
        }

    return app


app = create_app()
