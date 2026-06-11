from pathlib import Path

import uvicorn

from src.serving.app import create_application
from src.serving.json_lines_logger import JsonLinesLogger

MODEL_PATH = Path("artifacts/model.joblib")
REQUEST_LOG_PATH = Path("logs/requests.jsonl")
PREDICTION_LOG_PATH = Path("logs/predictions.jsonl")
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000


def main() -> None:
    application = create_application(
        MODEL_PATH,
        JsonLinesLogger(REQUEST_LOG_PATH),
        JsonLinesLogger(PREDICTION_LOG_PATH),
    )
    uvicorn.run(application, host=SERVER_HOST, port=SERVER_PORT)


if __name__ == "__main__":
    main()
