import sys

import uvicorn

from src.serving.model_server import create_model_application
from src.pipeline.config import (
    BLUE_MODEL_ENDPOINT,
    BLUE_TRAINING_CONFIG,
    GREEN_MODEL_ENDPOINT,
    GREEN_TRAINING_CONFIG,
)

MODEL_SERVERS = {
    "blue": (BLUE_MODEL_ENDPOINT, BLUE_TRAINING_CONFIG.artifacts_directory / "model.joblib"),
    "green": (GREEN_MODEL_ENDPOINT, GREEN_TRAINING_CONFIG.artifacts_directory / "model.joblib"),
}


def main(model_name: str) -> None:
    if model_name not in MODEL_SERVERS:
        raise ValueError(f"model_name must be one of {sorted(MODEL_SERVERS)}")
    endpoint, model_path = MODEL_SERVERS[model_name]
    application = create_model_application(model_path)
    uvicorn.run(application, host=endpoint.host, port=endpoint.port)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError("usage: uv run python -m src.serving.run_model_server <blue|green>")
    main(sys.argv[1])
