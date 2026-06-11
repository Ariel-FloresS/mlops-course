import base64
import json
from functools import cache
from pathlib import Path

import pandas as pd
from pydantic import ValidationError
from sklearn.pipeline import Pipeline

from src.model.persistence import load_model_pipeline
from src.serving.schemas import ChurnPredictionRequest

MODEL_PATH = Path("artifacts/model.joblib")


@cache
def get_model_pipeline(model_path: Path) -> Pipeline:
    return load_model_pipeline(model_path)


def predict_churn_probability(
    model_pipeline: Pipeline, request: ChurnPredictionRequest
) -> float:
    request_frame = pd.DataFrame([request.model_dump()])
    return float(model_pipeline.predict_proba(request_frame)[0, 1])


def parse_event_body(event: dict) -> dict:
    # TODO: raise ValueError containing "no body" when event has no "body"
    #       key or its value is None
    # TODO: if event says isBase64Encoded, base64-decode the body first
    # TODO: json.loads the body
    # TODO: raise ValueError containing "must be a JSON object" when the
    #       parsed body is not a dict
    # TODO: return the parsed dict
    raise NotImplementedError


def build_response(status_code: int, body: dict) -> dict:
    # TODO: return the API Gateway proxy response shape:
    #       statusCode, headers with Content-Type application/json,
    #       and body as a JSON STRING (json.dumps), not a dict
    raise NotImplementedError


def respond_to_event(model_pipeline: Pipeline, event: dict) -> dict:
    # TODO: parse the event body; a ValueError here means a client error,
    #       translate it into a 400 response with {"error": <message>}
    #       (the handler now plays the role FastAPI played in lessons 01-03)
    # TODO: validate the payload with ChurnPredictionRequest; a pydantic
    #       ValidationError translates into a 422 response with
    #       {"detail": validation_error.errors(include_url=False)}
    # TODO: predict, round the probability to 4 decimals, derive the label
    #       with the 0.5 threshold, return a 200 response with
    #       {"churn_probability": ..., "churn_label": ...}
    raise NotImplementedError


def handler(event: dict, context: object) -> dict:
    return respond_to_event(get_model_pipeline(MODEL_PATH), event)
