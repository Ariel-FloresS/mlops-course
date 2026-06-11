import sys
from dataclasses import replace
from pathlib import Path

from src.monitoring.alerts import enforce_monitoring_alerts
from src.monitoring.log_reader import read_json_lines
from src.monitoring.model_metrics import compute_model_metrics
from src.monitoring.report import render_html_report, render_text_report
from src.monitoring.service_metrics import compute_service_metrics
from src.pipeline.config import DEFAULT_MONITORING_CONFIG, MonitoringConfig


def run_monitoring_pipeline(config: MonitoringConfig) -> dict[str, dict]:
    request_records = read_json_lines(config.request_log_path)
    prediction_records = read_json_lines(config.prediction_log_path)
    print(
        f"read {len(request_records)} request records and "
        f"{len(prediction_records)} prediction records"
    )

    service_metrics = compute_service_metrics(request_records)
    model_metrics = compute_model_metrics(prediction_records)
    print(f"service metrics: {service_metrics}")
    print(f"model metrics: {model_metrics}")

    config.reports_directory.mkdir(parents=True, exist_ok=True)
    text_report_path = config.reports_directory / "monitoring_report.txt"
    html_report_path = config.reports_directory / "monitoring_report.html"
    text_report_path.write_text(render_text_report(service_metrics, model_metrics))
    html_report_path.write_text(render_html_report(service_metrics, model_metrics))
    print(f"reports written to {config.reports_directory}/")

    enforce_monitoring_alerts(service_metrics, model_metrics, config.thresholds)
    print("all monitoring alerts passed")
    return {"service": service_metrics, "model": model_metrics}


if __name__ == "__main__":
    if len(sys.argv) == 1:
        run_monitoring_pipeline(DEFAULT_MONITORING_CONFIG)
    elif len(sys.argv) == 3:
        run_monitoring_pipeline(
            replace(
                DEFAULT_MONITORING_CONFIG,
                request_log_path=Path(sys.argv[1]),
                prediction_log_path=Path(sys.argv[2]),
            )
        )
    else:
        raise ValueError(
            "usage: uv run python -m src.pipeline.monitoring_pipeline "
            "[<requests_log_path> <predictions_log_path>]"
        )
