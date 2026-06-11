import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

from src.data.loader import load_churn_frame
from src.data.schema_validator import validate_required_columns
from src.drift.drift_detector import compute_psi_by_feature
from src.drift.drift_gate import enforce_drift_gate
from src.drift.drift_report import render_drift_report
from src.drift.reference_profile import build_categorical_profile, build_numeric_profile
from src.monitoring.log_reader import read_json_lines
from src.pipeline.config import DEFAULT_DRIFT_CONFIG, DriftConfig


def run_drift_pipeline(config: DriftConfig) -> dict[str, float]:
    feature_columns = list(
        config.numeric_feature_columns + config.categorical_feature_columns
    )
    reference_frame = load_churn_frame(config.reference_dataset_path)
    validate_required_columns(reference_frame, feature_columns)
    print(
        f"built reference profiles from {config.reference_dataset_path} "
        f"({len(reference_frame)} rows)"
    )

    numeric_profiles = [
        build_numeric_profile(reference_frame[column], column, config.bin_count)
        for column in config.numeric_feature_columns
    ]
    categorical_profiles = [
        build_categorical_profile(reference_frame[column], column)
        for column in config.categorical_feature_columns
    ]

    prediction_records = read_json_lines(config.prediction_log_path)
    current_frame = pd.DataFrame(prediction_records)
    validate_required_columns(current_frame, feature_columns)
    print(f"read {len(current_frame)} current records from {config.prediction_log_path}")

    psi_by_feature = compute_psi_by_feature(
        numeric_profiles, categorical_profiles, current_frame
    )
    print(f"psi by feature: {psi_by_feature}")

    config.reports_directory.mkdir(parents=True, exist_ok=True)
    report_path = config.reports_directory / "drift_report.txt"
    report_path.write_text(
        render_drift_report(
            psi_by_feature, config.maximum_psi, len(reference_frame), len(current_frame)
        )
    )
    print(f"report written to {report_path}")

    enforce_drift_gate(psi_by_feature, config.maximum_psi)
    print(f"no drift detected: all features below psi threshold {config.maximum_psi}")
    return psi_by_feature


if __name__ == "__main__":
    if len(sys.argv) == 1:
        run_drift_pipeline(DEFAULT_DRIFT_CONFIG)
    elif len(sys.argv) == 2:
        run_drift_pipeline(
            replace(DEFAULT_DRIFT_CONFIG, prediction_log_path=Path(sys.argv[1]))
        )
    else:
        raise ValueError(
            "usage: uv run python -m src.pipeline.drift_pipeline [<prediction_log_path>]"
        )
