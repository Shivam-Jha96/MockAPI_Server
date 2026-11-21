"""Routes package."""
from src.routes.webhooks import router as webhooks_router
from src.routes.meta_graph import router as meta_graph_router
from src.routes.nlu import router as nlu_router
from src.routes.kms import router as kms_router
from src.routes.observability import router as observability_router
from src.routes.simulator import router as simulator_router

__all__ = [
    "webhooks_router",
    "meta_graph_router",
    "nlu_router",
    "kms_router",
    "observability_router",
    "simulator_router",
]
