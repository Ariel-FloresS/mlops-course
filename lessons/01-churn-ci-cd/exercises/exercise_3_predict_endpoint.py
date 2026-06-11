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
    # TODO: turn the request into a one-row DataFrame (hint: request.model_dump())
    # TODO: return the positive-class probability from predict_proba as a float
    raise NotImplementedError


def create_application(model_path: Path) -> FastAPI:
    # TODO: load the model pipeline ONCE here, so every request reuses it
    # TODO: build the FastAPI application
    # TODO: register GET /health returning HealthResponse(status="ok")
    # TODO: register POST /predict that:
    #       1. calls predict_churn_probability
    #       2. rounds the probability to 4 decimals
    #       3. derives churn_label with a 0.5 threshold
    #       4. returns a ChurnPredictionResponse
    # TODO: return the application
    raise NotImplementedError
