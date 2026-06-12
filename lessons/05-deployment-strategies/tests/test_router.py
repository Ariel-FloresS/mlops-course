import json

import pytest
from fastapi.testclient import TestClient

from src.deployment.routing_config import ModelEndpoint, RoutingConfig
from src.serving.json_lines_logger import JsonLinesLogger
from src.serving.router import create_router_application

BLUE_ENDPOINT = ModelEndpoint(name="blue", host="127.0.0.1", port=8001)
GREEN_ENDPOINT = ModelEndpoint(name="green", host="127.0.0.1", port=8002)

PREDICTIONS_BY_ENDPOINT = {
    "blue": {"churn_probability": 0.9, "churn_label": 1},
    "green": {"churn_probability": 0.4, "churn_label": 0},
}


def fake_forwarder(endpoint: ModelEndpoint, request_body: dict) -> dict:
    return PREDICTIONS_BY_ENDPOINT[endpoint.name]


def build_client(mode: str, shadow_log_path, canary_green_weight: float = 0.2) -> TestClient:
    routing_config = RoutingConfig(
        mode=mode, canary_green_weight=canary_green_weight, splitter_seed=13
    )
    application = create_router_application(
        routing_config,
        BLUE_ENDPOINT,
        GREEN_ENDPOINT,
        JsonLinesLogger(shadow_log_path),
        fake_forwarder,
    )
    return TestClient(application)


def build_request_body() -> dict:
    return {
        "tenure_months": 2,
        "monthly_charges": 95.0,
        "total_charges": 190.0,
        "contract_type": "month_to_month",
        "payment_method": "electronic_check",
        "support_tickets": 4,
    }


def test_blue_mode_routes_to_blue_with_header(tmp_path):
    client = build_client("blue", tmp_path / "shadow.jsonl")
    response = client.post("/predict", json=build_request_body())
    assert response.status_code == 200
    assert response.headers["x-served-by"] == "blue"
    assert response.json() == PREDICTIONS_BY_ENDPOINT["blue"]


def test_canary_with_full_weight_routes_to_green(tmp_path):
    client = build_client("canary", tmp_path / "shadow.jsonl", canary_green_weight=1.0)
    response = client.post("/predict", json=build_request_body())
    assert response.headers["x-served-by"] == "green"
    assert response.json() == PREDICTIONS_BY_ENDPOINT["green"]


def test_shadow_mode_returns_blue_and_logs_both_predictions(tmp_path):
    shadow_log_path = tmp_path / "shadow.jsonl"
    client = build_client("shadow", shadow_log_path)
    response = client.post("/predict", json=build_request_body())
    assert response.headers["x-served-by"] == "blue"
    assert response.json() == PREDICTIONS_BY_ENDPOINT["blue"]
    shadow_record = json.loads(shadow_log_path.read_text().splitlines()[0])
    assert shadow_record["blue_probability"] == 0.9
    assert shadow_record["green_probability"] == 0.4
    assert shadow_record["blue_label"] == 1
    assert shadow_record["green_label"] == 0
    assert shadow_record["contract_type"] == "month_to_month"


def test_unknown_routing_mode_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="routing mode must be one of"):
        build_client("purple", tmp_path / "shadow.jsonl")
