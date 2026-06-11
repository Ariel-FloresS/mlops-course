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
    # TODO: return a dict with keys timestamp (UTC ISO format), method, path,
    #       status_code, latency_ms
    raise NotImplementedError


def build_prediction_record(
    request: ChurnPredictionRequest, churn_probability: float, churn_label: int
) -> dict:
    # TODO: return a dict with timestamp (UTC ISO format), every request field
    #       (hint: **request.model_dump()), churn_probability, churn_label
    raise NotImplementedError


def create_application(
    model_path: Path,
    request_logger: JsonLinesLogger,
    prediction_logger: JsonLinesLogger,
) -> FastAPI:
    model_pipeline = load_model_pipeline(model_path)
    application = FastAPI(title="churn-prediction-service")

    # TODO: register an http middleware that:
    #       1. captures time.perf_counter() before calling call_next
    #       2. awaits call_next(request) to get the response
    #       3. computes latency_ms rounded to 2 decimals
    #       4. writes build_request_record(...) through request_logger
    #          (this must run for EVERY request, including 422 rejections)
    #       5. returns the response

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.post("/predict", response_model=ChurnPredictionResponse)
    def predict(request: ChurnPredictionRequest) -> ChurnPredictionResponse:
        churn_probability = round(predict_churn_probability(model_pipeline, request), 4)
        churn_label = int(churn_probability >= 0.5)
        # TODO: write build_prediction_record(...) through prediction_logger
        return ChurnPredictionResponse(
            churn_probability=churn_probability, churn_label=churn_label
        )

    return application
