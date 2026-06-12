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
    # TODO: return a dict with: timestamp (UTC ISO format), every request
    #       field (**request.model_dump()), blue_probability, blue_label,
    #       green_probability, green_label
    raise NotImplementedError


def create_router_application(
    routing_config: RoutingConfig,
    blue_endpoint: ModelEndpoint,
    green_endpoint: ModelEndpoint,
    shadow_logger: JsonLinesLogger,
    forwarder: Callable[[ModelEndpoint, dict], dict],
) -> FastAPI:
    # TODO: raise ValueError ("routing mode must be one of ...") when
    #       routing_config.mode is not in ROUTING_MODES
    # TODO: build a WeightedTrafficSplitter from the config's
    #       canary_green_weight and splitter_seed
    application = FastAPI(title="churn-routing-service")

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @application.post("/predict", response_model=ChurnPredictionResponse)
    def predict(request: ChurnPredictionRequest, response: Response) -> ChurnPredictionResponse:
        # TODO (shadow mode): forward to BOTH endpoints, write a shadow
        #       record through shadow_logger, set the X-Served-By header to
        #       blue's name, and return BLUE's prediction (green's response
        #       is observed, never served)
        # TODO (canary mode): ask the splitter which target serves this request
        # TODO (blue / green modes): the mode name IS the target name —
        #       that one line is the whole blue-green switch
        # TODO: forward to the chosen endpoint, set X-Served-By to the
        #       target name, return the prediction
        raise NotImplementedError

    return application
