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
    if event.get("body") is None:
        raise ValueError("event has no body")
    raw_body = event["body"]
    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body).decode()
    parsed_body = json.loads(raw_body)
    if not isinstance(parsed_body, dict):
        raise ValueError("body must be a JSON object")
    return parsed_body


def build_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def respond_to_event(model_pipeline: Pipeline, event: dict) -> dict:
    try:
        payload = parse_event_body(event)
    except ValueError as parse_error:
        return build_response(400, {"error": str(parse_error)})
    try:
        request = ChurnPredictionRequest(**payload)
    except ValidationError as validation_error:
        return build_response(
            422, {"detail": validation_error.errors(include_url=False)}
        )
    churn_probability = round(predict_churn_probability(model_pipeline, request), 4)
    return build_response(
        200,
        {
            "churn_probability": churn_probability,
            "churn_label": int(churn_probability >= 0.5),
        },
    )


def handler(event: dict, context: object) -> dict:
    return respond_to_event(get_model_pipeline(MODEL_PATH), event)
