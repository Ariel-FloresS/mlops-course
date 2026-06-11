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
    # TODO: build a list with one human-readable string per violated threshold:
    #       1. error_rate above max_error_rate
    #          ("error_rate=X exceeds maximum Y")
    #       2. latency_ms_p95 above max_latency_ms_p95
    #          ("latency_ms_p95=X exceeds maximum Y")
    #       3. prediction_count below min_prediction_count
    #          ("prediction_count=X is below minimum Y")
    #       4. mean_probability outside [min_mean_probability, max_mean_probability]
    #          ("mean_probability=X is outside [A, B]")
    # TODO: return the list (empty when everything is healthy)
    raise NotImplementedError


def enforce_monitoring_alerts(
    service_metrics: dict, model_metrics: dict, thresholds: MonitoringThresholds
) -> None:
    # TODO: collect the violations; if there are any, raise ValueError
    #       with a message starting with "monitoring alerts fired:"
    #       that lists every violation
    raise NotImplementedError
