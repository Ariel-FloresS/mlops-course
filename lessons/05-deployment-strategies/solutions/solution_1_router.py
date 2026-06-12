import http.client
import json
from datetime import datetime, timezone
from typing import Callable

from fastapi import FastAPI, Response

from src.deployment.routing_config import ROUTING_MODES, ModelEndpoint, RoutingConfig
from src.deployment.traffic_splitter import WeightedTrafficSplitter
from src.serving.json_lines_logger import JsonLinesLogger
from src.serving.schemas import (
    ChurnPredictionRequest,
    ChurnPredictionResponse,
    HealthResponse,
)


def forward_predict_request(endpoint: ModelEndpoint, request_body: dict) -> dict:
    connection = http.client.HTTPConnection(endpoint.host, endpoint.port)
    connection.request(
        "POST",
        "/predict",
        body=json.dumps(request_body),
        headers={"Content-Type": "application/json"},
    )
    response = connection.getresponse()
    response_body = response.read()
    connection.close()
    if response.status != 200:
        raise ValueError(f"{endpoint.name} model server returned status {response.status}")
    return json.loads(response_body)


def build_shadow_record(
    request: ChurnPredictionRequest, blue_prediction: dict, green_prediction: dict
) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **request.model_dump(),
        "blue_probability": blue_prediction["churn_probability"],
        "blue_label": blue_prediction["churn_label"],
        "green_probability": green_prediction["churn_probability"],
        "green_label": green_prediction["churn_label"],
    }


def create_router_application(
    routing_config: RoutingConfig,
    blue_endpoint: ModelEndpoint,
    green_endpoint: ModelEndpoint,
    shadow_logger: JsonLinesLogger,
    forwarder: Callable[[ModelEndpoint, dict], dict],
) -> FastAPI:
    if routing_config.mode not in ROUTING_MODES:
        raise ValueError(
            f"routing mode must be one of {ROUTING_MODES}, got {routing_config.mode}"
        )
    traffic_splitter = WeightedTrafficSplitter(
        routing_config.canary_green_weight, routing_config.splitter_seed
    )
    endpoints_by_name = {"blue": blue_endpoint, "green": green_endpoint}
    application = FastAPI(title="churn-routing-service")

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.post("/predict", response_model=ChurnPredictionResponse)
    def predict(request: ChurnPredictionRequest, response: Response) -> ChurnPredictionResponse:
        if routing_config.mode == "shadow":
            blue_prediction = forwarder(blue_endpoint, request.model_dump())
            green_prediction = forwarder(green_endpoint, request.model_dump())
            shadow_logger.write_record(
                build_shadow_record(request, blue_prediction, green_prediction)
            )
            response.headers["X-Served-By"] = blue_endpoint.name
            return ChurnPredictionResponse(**blue_prediction)
        if routing_config.mode == "canary":
            target_name = traffic_splitter.choose_target()
        else:
            target_name = routing_config.mode
        prediction = forwarder(endpoints_by_name[target_name], request.model_dump())
        response.headers["X-Served-By"] = target_name
        return ChurnPredictionResponse(**prediction)

    return application
