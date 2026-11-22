"""Modal serverless deployment wrapper for Mock API Server."""
import sys
from pathlib import Path
import modal

app_name = "mockapi-server"

# Container image definition with all dependencies installed and src baked in
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
    .add_local_python_source("src", copy=True)
)

modal_app = modal.App(name=app_name, image=image)
app = modal_app


@modal_app.function(image=image, max_containers=1)
@modal.asgi_app()
def fastapi_app():
    """ASGI entrypoint exposed to the internet via Modal serverless HTTPS endpoint."""
    # Ensure current directory (/root in container) is on sys.path
    current_dir = str(Path(__file__).resolve().parent)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from src.app import create_app
    return create_app()
