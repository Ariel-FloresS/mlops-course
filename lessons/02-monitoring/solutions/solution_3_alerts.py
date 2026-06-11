from dataclasses import dataclass


@dataclass(frozen=True)
class MonitoringThresholds:
    max_error_rate: float
    max_latency_ms_p95: float
    min_prediction_count: int
    min_mean_probability: float
    max_mean_probability: float


def collect_alert_violations(
    service_metrics: dict, model_metrics: dict, thresholds: MonitoringThresholds
) -> list[str]:
    violations = []
    if service_metrics["error_rate"] > thresholds.max_error_rate:
        violations.append(
            f"error_rate={service_metrics['error_rate']} exceeds maximum {thresholds.max_error_rate}"
        )
    if service_metrics["latency_ms_p95"] > thresholds.max_latency_ms_p95:
        violations.append(
            f"latency_ms_p95={service_metrics['latency_ms_p95']} exceeds maximum {thresholds.max_latency_ms_p95}"
        )
    if model_metrics["prediction_count"] < thresholds.min_prediction_count:
        violations.append(
            f"prediction_count={model_metrics['prediction_count']} is below minimum {thresholds.min_prediction_count}"
        )
    mean_probability = model_metrics["mean_probability"]
    if not thresholds.min_mean_probability <= mean_probability <= thresholds.max_mean_probability:
        violations.append(
            f"mean_probability={mean_probability} is outside "
            f"[{thresholds.min_mean_probability}, {thresholds.max_mean_probability}]"
        )
    return violations


def enforce_monitoring_alerts(
    service_metrics: dict, model_metrics: dict, thresholds: MonitoringThresholds
) -> None:
    violations = collect_alert_violations(service_metrics, model_metrics, thresholds)
    if violations:
        raise ValueError(f"monitoring alerts fired: {violations}")
