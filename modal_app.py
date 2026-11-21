"""Modal serverless deployment wrapper for Mock API Server."""
import modal
from src.app import create_app

app_name = "mockapi-server"

# Container image definition with all dependencies installed
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "pydantic>=2.8.0",
        "cryptography>=43.0.0",
        "prometheus-client>=0.20.0",
        "python-multipart>=0.0.9",
        "httpx>=0.27.0",
    )
    .add_local_python_source("src")
)

modal_app = modal.App(name=app_name, image=image)
app = modal_app


# Set concurrency_limit=1 (renamed to max_containers=1 in Modal 1.x) to guarantee single-container state consistency
try:
    _function_decorator = modal_app.function(max_containers=1)
except Exception:
    _function_decorator = modal_app.function(concurrency_limit=1)


@_function_decorator
@modal.asgi_app()
def fastapi_app():
    """ASGI entrypoint exposed to the internet via Modal serverless HTTPS endpoint."""
    return create_app()
