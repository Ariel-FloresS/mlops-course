from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from sklearn.pipeline import Pipeline

from src.model.persistence import load_model_pipeline
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


def create_application(model_path: Path) -> FastAPI:
    model_pipeline = load_model_pipeline(model_path)
    application = FastAPI(title="churn-prediction-service")

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.post("/predict", response_model=ChurnPredictionResponse)
    def predict(request: ChurnPredictionRequest) -> ChurnPredictionResponse:
        churn_probability = predict_churn_probability(model_pipeline, request)
        return ChurnPredictionResponse(
            churn_probability=round(churn_probability, 4),
            churn_label=int(churn_probability >= 0.5),
        )

    return application
