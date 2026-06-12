import sys
from dataclasses import replace

import uvicorn

from src.deployment.routing_config import ROUTING_MODES
from src.serving.json_lines_logger import JsonLinesLogger
from src.serving.router import create_router_application, forward_predict_request
from src.pipeline.config import (
    BLUE_MODEL_ENDPOINT,
    DEFAULT_ROUTING_CONFIG,
    GREEN_MODEL_ENDPOINT,
    SHADOW_LOG_PATH,
)

ROUTER_HOST = "127.0.0.1"
ROUTER_PORT = 8000


def main(mode: str) -> None:
    routing_config = replace(DEFAULT_ROUTING_CONFIG, mode=mode)
    application = create_router_application(
        routing_config,
        BLUE_MODEL_ENDPOINT,
        GREEN_MODEL_ENDPOINT,
        JsonLinesLogger(SHADOW_LOG_PATH),
        forward_predict_request,
    )
    print(f"routing mode: {mode}")
    uvicorn.run(application, host=ROUTER_HOST, port=ROUTER_PORT)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ROUTING_MODES:
        raise ValueError(
            f"usage: uv run python -m src.serving.run_router <{'|'.join(ROUTING_MODES)}>"
        )
    main(sys.argv[1])
