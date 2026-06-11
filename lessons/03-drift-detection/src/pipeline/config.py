from dataclasses import dataclass
from pathlib import Path


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
class DriftConfig:
    reference_dataset_path: Path
    prediction_log_path: Path
    reports_directory: Path
    numeric_feature_columns: tuple[str, ...]
    categorical_feature_columns: tuple[str, ...]
    bin_count: int
    maximum_psi: float


DEFAULT_DRIFT_CONFIG = DriftConfig(
    reference_dataset_path=Path("data/churn.csv"),
    prediction_log_path=Path("logs/predictions.jsonl"),
    reports_directory=Path("reports"),
    numeric_feature_columns=(
        "tenure_months",
        "monthly_charges",
        "total_charges",
        "support_tickets",
    ),
    categorical_feature_columns=("contract_type", "payment_method"),
    bin_count=10,
    maximum_psi=0.2,
)
