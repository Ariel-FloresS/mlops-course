from dataclasses import dataclass

ROUTING_MODES = ("blue", "green", "canary", "shadow")


@dataclass(frozen=True)
class ModelEndpoint:
    name: str
    host: str
    port: int


@dataclass(frozen=True)
class RoutingConfig:
    mode: str
    canary_green_weight: float
    splitter_seed: int
