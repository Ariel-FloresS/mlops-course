import sys
from dataclasses import asdict, replace
from pathlib import Path

from src.deployment.promotion_gate import enforce_promotion_gate
from src.deployment.promotion_report import render_promotion_report
from src.deployment.shadow_comparator import compare_shadow_records
from src.monitoring.log_reader import read_json_lines
from src.pipeline.config import DEFAULT_PROMOTION_CONFIG, PromotionConfig


def run_promotion_pipeline(config: PromotionConfig) -> dict:
    shadow_records = read_json_lines(config.shadow_log_path)
    print(f"read {len(shadow_records)} shadow comparison records from {config.shadow_log_path}")

    comparison_metrics = compare_shadow_records(shadow_records)
    print(f"comparison metrics: {comparison_metrics}")

    config.reports_directory.mkdir(parents=True, exist_ok=True)
    report_path = config.reports_directory / "promotion_report.txt"
    report_path.write_text(
        render_promotion_report(comparison_metrics, asdict(config.thresholds))
    )
    print(f"report written to {report_path}")

    enforce_promotion_gate(comparison_metrics, config.thresholds)
    print("promotion gate passed: green is safe to receive traffic")
    return comparison_metrics


if __name__ == "__main__":
    if len(sys.argv) == 1:
        run_promotion_pipeline(DEFAULT_PROMOTION_CONFIG)
    elif len(sys.argv) == 2:
        run_promotion_pipeline(
            replace(DEFAULT_PROMOTION_CONFIG, shadow_log_path=Path(sys.argv[1]))
        )
    else:
        raise ValueError(
            "usage: uv run python -m src.pipeline.promotion_pipeline [<shadow_log_path>]"
        )
