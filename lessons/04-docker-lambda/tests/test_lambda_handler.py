import base64
import json
from pathlib import Path

import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.features.encoder import build_feature_encoder
from src.model.trainer import build_model_pipeline, train_model_pipeline
from src.serving.lambda_handler import parse_event_body, respond_to_event

NUMERIC_COLUMNS = ["tenure_months", "monthly_charges", "total_charges", "support_tickets"]
CATEGORICAL_COLUMNS = ["contract_type", "payment_method"]
EVENTS_DIRECTORY = Path(__file__).parent.parent / "events"


def build_tiny_training_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "tenure_months": [1, 50, 3, 60, 2, 45, 5, 70, 4, 65, 6, 40],
            "monthly_charges": [90.0, 30.0, 85.0, 25.0, 95.0, 35.0, 80.0, 20.0, 88.0, 28.0, 75.0, 40.0],
            "total_charges": [90.0, 1500.0, 255.0, 1500.0, 190.0, 1575.0, 400.0, 1400.0, 352.0, 1820.0, 450.0, 1600.0],
            "contract_type": [
                "month_to_month", "two_year", "month_to_month", "two_year",
                "month_to_month", "one_year", "month_to_month", "two_year",
                "one_year", "two_year", "month_to_month", "one_year",
            ],
            "payment_method": [
                "electronic_check", "credit_card", "electronic_check", "bank_transfer",
                "electronic_check", "credit_card", "bank_transfer", "credit_card",
                "electronic_check", "bank_transfer", "credit_card", "bank_transfer",
            ],
            "support_tickets": [5, 0, 4, 0, 6, 1, 3, 0, 4, 1, 2, 1],
            "churn": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0],
        }
    )


@pytest.fixture
def model_pipeline():
    frame = build_tiny_training_frame()
    feature_encoder = build_feature_encoder(NUMERIC_COLUMNS, CATEGORICAL_COLUMNS)
    classifier = LogisticRegression(max_iter=1000, random_state=0)
    pipeline = build_model_pipeline(feature_encoder, classifier)
    return train_model_pipeline(
        pipeline, frame[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS], frame["churn"]
    )


def load_event(event_file_name: str) -> dict:
    return json.loads((EVENTS_DIRECTORY / event_file_name).read_text())


def test_parse_rejects_event_without_body():
    with pytest.raises(ValueError, match="no body"):
        parse_event_body({"version": "2.0"})


def test_parse_rejects_non_object_body():
    with pytest.raises(ValueError, match="must be a JSON object"):
        parse_event_body({"body": "[1, 2, 3]"})


def test_parse_decodes_base64_body():
    encoded_body = base64.b64encode(b'{"tenure_months": 2}').decode()
    parsed = parse_event_body({"body": encoded_body, "isBase64Encoded": True})
    assert parsed == {"tenure_months": 2}


def test_predict_event_returns_api_gateway_shaped_200(model_pipeline):
    response = respond_to_event(model_pipeline, load_event("predict_high_risk.json"))
    assert response["statusCode"] == 200
    assert response["headers"] == {"Content-Type": "application/json"}
    body = json.loads(response["body"])
    assert set(body) == {"churn_probability", "churn_label"}
    assert 0.0 <= body["churn_probability"] <= 1.0
    assert body["churn_label"] == int(body["churn_probability"] >= 0.5)


def test_invalid_contract_event_returns_422_with_detail(model_pipeline):
    response = respond_to_event(
        model_pipeline, load_event("predict_invalid_contract.json")
    )
    assert response["statusCode"] == 422
    body = json.loads(response["body"])
    assert body["detail"][0]["loc"] == ["contract_type"]


def test_malformed_json_body_returns_400(model_pipeline):
    response = respond_to_event(model_pipeline, {"body": "{not json"})
    assert response["statusCode"] == 400


def test_event_without_body_returns_400(model_pipeline):
    response = respond_to_event(model_pipeline, {"version": "2.0"})
    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"error": "event has no body"}
