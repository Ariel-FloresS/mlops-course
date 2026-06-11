from dataclasses import dataclass
from pathlib import Path

from src.monitoring.alerts import MonitoringThresholds


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


DEFAULT_TRAINING_CONFIG = TrainingConfig(
    dataset_path=Path("data/churn.csv"),
    artifacts_directory=Path("artifacts"),
    numeric_feature_columns=(
        "tenure_months",
        "monthly_charges",
        "total_charges",
        "support_tickets",
    ),
    categorical_feature_columns=("contract_type", "payment_method"),
    target_column="churn",
    test_fraction=0.2,
    seed=42,
    gate_metric_name="roc_auc",
    gate_minimum_value=0.85,
)


@dataclass(frozen=True)
class MonitoringConfig:
    request_log_path: Path
    prediction_log_path: Path
    reports_directory: Path
    thresholds: MonitoringThresholds


DEFAULT_MONITORING_CONFIG = MonitoringConfig(
    request_log_path=Path("logs/requests.jsonl"),
    prediction_log_path=Path("logs/predictions.jsonl"),
    reports_directory=Path("reports"),
    thresholds=MonitoringThresholds(
        max_error_rate=0.05,
        max_latency_ms_p95=500.0,
        min_prediction_count=150,
        min_mean_probability=0.15,
        max_mean_probability=0.55,
    ),
)
