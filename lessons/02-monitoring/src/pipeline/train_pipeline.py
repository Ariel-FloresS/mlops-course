from sklearn.linear_model import LogisticRegression

from src.data.loader import load_churn_frame
from src.data.schema_validator import (
    validate_binary_target,
    validate_no_missing_values,
    validate_required_columns,
)
from src.data.splitter import split_features_and_target, split_train_test
from src.features.encoder import build_feature_encoder
from src.model.evaluator import evaluate_classifier
from src.model.metric_gate import enforce_metric_gate
from src.model.persistence import save_metrics, save_model_pipeline
from src.model.trainer import build_model_pipeline, train_model_pipeline
from src.pipeline.config import DEFAULT_TRAINING_CONFIG, TrainingConfig


def run_training_pipeline(config: TrainingConfig) -> dict[str, float]:
    frame = load_churn_frame(config.dataset_path)
    feature_columns = list(
        config.numeric_feature_columns + config.categorical_feature_columns
    )
    validate_required_columns(frame, feature_columns + [config.target_column])
    validate_no_missing_values(frame, feature_columns + [config.target_column])
    validate_binary_target(frame, config.target_column)
    print(f"loaded {len(frame)} rows from {config.dataset_path}")

    features, target = split_features_and_target(
        frame, feature_columns, config.target_column
    )
    train_features, test_features, train_target, test_target = split_train_test(
        features, target, config.test_fraction, config.seed
    )
    print(f"split into {len(train_features)} train rows and {len(test_features)} test rows")

    feature_encoder = build_feature_encoder(
        list(config.numeric_feature_columns), list(config.categorical_feature_columns)
    )
    classifier = LogisticRegression(max_iter=1000, random_state=config.seed)
    model_pipeline = build_model_pipeline(feature_encoder, classifier)
    train_model_pipeline(model_pipeline, train_features, train_target)
    print("training complete")

    metrics = evaluate_classifier(model_pipeline, test_features, test_target)
    print(f"test metrics: {metrics}")
    enforce_metric_gate(metrics, config.gate_metric_name, config.gate_minimum_value)
    print(f"metric gate passed: {config.gate_metric_name} >= {config.gate_minimum_value}")

    save_model_pipeline(model_pipeline, config.artifacts_directory / "model.joblib")
    save_metrics(metrics, config.artifacts_directory / "metrics.json")
    print(f"artifacts written to {config.artifacts_directory}/")
    return metrics


if __name__ == "__main__":
    run_training_pipeline(DEFAULT_TRAINING_CONFIG)
