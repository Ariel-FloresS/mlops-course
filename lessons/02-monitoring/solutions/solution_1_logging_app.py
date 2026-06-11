import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Request
from sklearn.pipeline import Pipeline

from src.model.persistence import load_model_pipeline
from src.serving.json_lines_logger import JsonLinesLogger
from src.serving.schemas import (
    ChurnPredictionRequest,
    ChurnPredictionResponse,
    HealthResponse,
)


def predict_churn_probability(
    model_pipeline: Pipeline, request: ChurnPredictionRequest
) -> float:
    request_frame = pd.DataFrame([request.model_dump()])
    return float(model_pipeline.predict_proba(request_frame)[0, 1])


def build_request_record(
    method: str, path: str, status_code: int, latency_ms: float
) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "path": path,
        "status_code": status_code,
        "latency_ms": latency_ms,
    }


def build_prediction_record(
    request: ChurnPredictionRequest, churn_probability: float, churn_label: int
) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **request.model_dump(),
        "churn_probability": churn_probability,
        "churn_label": churn_label,
    }


def create_application(
    model_path: Path,
    request_logger: JsonLinesLogger,
    prediction_logger: JsonLinesLogger,
) -> FastAPI:
    model_pipeline = load_model_pipeline(model_path)
    application = FastAPI(title="churn-prediction-service")

    @application.middleware("http")
    async def log_request(request: Request, call_next):
        started_at = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        request_logger.write_record(
            build_request_record(
                request.method, request.url.path, response.status_code, latency_ms
            )
        )
        return response

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.post("/predict", response_model=ChurnPredictionResponse)
    def predict(request: ChurnPredictionRequest) -> ChurnPredictionResponse:
        churn_probability = round(predict_churn_probability(model_pipeline, request), 4)
        churn_label = int(churn_probability >= 0.5)
        prediction_logger.write_record(
            build_prediction_record(request, churn_probability, churn_label)
        )
        return ChurnPredictionResponse(
            churn_probability=churn_probability, churn_label=churn_label
        )

    return application
