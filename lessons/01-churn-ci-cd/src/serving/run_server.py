from pathlib import Path

import uvicorn

from src.serving.app import create_application

MODEL_PATH = Path("artifacts/model.joblib")
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000


def main() -> None:
    application = create_application(MODEL_PATH)
    uvicorn.run(application, host=SERVER_HOST, port=SERVER_PORT)


if __name__ == "__main__":
    main()
