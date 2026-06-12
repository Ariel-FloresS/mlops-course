from dataclasses import dataclass
from pathlib import Path

from src.deployment.promotion_gate import PromotionThresholds
from src.deployment.routing_config import ModelEndpoint, RoutingConfig


@dataclass(frozen=True)
class TrainingConfig:
    dataset_path: Path
    artifacts_directory: Path
    numeric_feature_columns: tuple[str, ...]
    categorical_feature_columns: tuple[str, ...]
    target_column: str
    test_fraction: float
    seed: int
    gate_metric_name: str
    gate_minimum_value: float


FEATURE_COLUMNS = {
    "numeric_feature_columns": (
        "tenure_months",
        "monthly_charges",
        "total_charges",
        "support_tickets",
    ),
    "categorical_feature_columns": ("contract_type", "payment_method"),
}

BLUE_TRAINING_CONFIG = TrainingConfig(
    dataset_path=Path("data/churn.csv"),
    artifacts_directory=Path("artifacts/blue"),
    target_column="churn",
    test_fraction=0.2,
    seed=42,
    gate_metric_name="roc_auc",
    gate_minimum_value=0.85,
    **FEATURE_COLUMNS,
)

GREEN_TRAINING_CONFIG = TrainingConfig(
    dataset_path=Path("data/churn_v2.csv"),
    artifacts_directory=Path("artifacts/green"),
    target_column="churn",
    test_fraction=0.2,
    seed=42,
    gate_metric_name="roc_auc",
    gate_minimum_value=0.85,
    **FEATURE_COLUMNS,
)

BLUE_MODEL_ENDPOINT = ModelEndpoint(name="blue", host="127.0.0.1", port=8001)
GREEN_MODEL_ENDPOINT = ModelEndpoint(name="green", host="127.0.0.1", port=8002)

DEFAULT_ROUTING_CONFIG = RoutingConfig(
    mode="blue",
    canary_green_weight=0.2,
    splitter_seed=13,
)

SHADOW_LOG_PATH = Path("logs/shadow_predictions.jsonl")


@dataclass(frozen=True)
class PromotionConfig:
    shadow_log_path: Path
    reports_directory: Path
    thresholds: PromotionThresholds


DEFAULT_PROMOTION_CONFIG = PromotionConfig(
    shadow_log_path=SHADOW_LOG_PATH,
    reports_directory=Path("reports"),
    thresholds=PromotionThresholds(
        min_label_agreement_rate=0.9,
        max_mean_probability_delta=0.1,
        min_comparison_count=150,
    ),
)
