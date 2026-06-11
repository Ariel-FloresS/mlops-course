import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from src.features.encoder import build_feature_encoder
from src.model.persistence import save_model_pipeline
from src.model.trainer import build_model_pipeline, train_model_pipeline
from src.serving.app import create_application
from src.serving.json_lines_logger import JsonLinesLogger

NUMERIC_COLUMNS = ["tenure_months", "monthly_charges", "total_charges", "support_tickets"]
CATEGORICAL_COLUMNS = ["contract_type", "payment_method"]


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
def serving_paths(tmp_path):
    frame = build_tiny_training_frame()
    feature_encoder = build_feature_encoder(NUMERIC_COLUMNS, CATEGORICAL_COLUMNS)
    classifier = LogisticRegression(max_iter=1000, random_state=0)
    model_pipeline = build_model_pipeline(feature_encoder, classifier)
    train_model_pipeline(
        model_pipeline, frame[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS], frame["churn"]
    )
    model_path = tmp_path / "model.joblib"
    save_model_pipeline(model_pipeline, model_path)
    request_log_path = tmp_path / "requests.jsonl"
    prediction_log_path = tmp_path / "predictions.jsonl"
    application = create_application(
        model_path,
        JsonLinesLogger(request_log_path),
        JsonLinesLogger(prediction_log_path),
    )
    return TestClient(application), request_log_path, prediction_log_path


def build_request_body() -> dict:
    return {
        "tenure_months": 2,
        "monthly_charges": 95.0,
        "total_charges": 190.0,
        "contract_type": "month_to_month",
        "payment_method": "electronic_check",
        "support_tickets": 4,
    }


def test_predict_writes_request_and_prediction_records(serving_paths):
    client, request_log_path, prediction_log_path = serving_paths
    response = client.post("/predict", json=build_request_body())
    assert response.status_code == 200
    request_record = json.loads(request_log_path.read_text().splitlines()[0])
    assert request_record["path"] == "/predict"
    assert request_record["status_code"] == 200
    assert request_record["latency_ms"] >= 0
    prediction_record = json.loads(prediction_log_path.read_text().splitlines()[0])
    assert prediction_record["contract_type"] == "month_to_month"
    assert prediction_record["churn_probability"] == response.json()["churn_probability"]
    assert prediction_record["churn_label"] == response.json()["churn_label"]


def test_invalid_request_logs_422_without_prediction_record(serving_paths):
    client, request_log_path, prediction_log_path = serving_paths
    invalid_body = build_request_body() | {"contract_type": "weekly"}
    response = client.post("/predict", json=invalid_body)
    assert response.status_code == 422
    request_record = json.loads(request_log_path.read_text().splitlines()[0])
    assert request_record["status_code"] == 422
    assert not prediction_log_path.exists()


def test_health_request_is_logged(serving_paths):
    client, request_log_path, prediction_log_path = serving_paths
    response = client.get("/health")
    assert response.status_code == 200
    request_record = json.loads(request_log_path.read_text().splitlines()[0])
    assert request_record["path"] == "/health"
    assert request_record["method"] == "GET"
