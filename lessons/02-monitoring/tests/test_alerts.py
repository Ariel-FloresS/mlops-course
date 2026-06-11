import pytest

from src.monitoring.alerts import (
    MonitoringThresholds,
    collect_alert_violations,
    enforce_monitoring_alerts,
)

THRESHOLDS = MonitoringThresholds(
    max_error_rate=0.05,
    max_latency_ms_p95=500.0,
    min_prediction_count=150,
    min_mean_probability=0.15,
    max_mean_probability=0.55,
)


def build_healthy_service_metrics() -> dict:
    return {"error_rate": 0.04, "latency_ms_p95": 12.5}


def build_healthy_model_metrics() -> dict:
    return {"prediction_count": 192, "mean_probability": 0.33}


def test_healthy_metrics_produce_no_violations_and_pass():
    violations = collect_alert_violations(
        build_healthy_service_metrics(), build_healthy_model_metrics(), THRESHOLDS
    )
    assert violations == []
    enforce_monitoring_alerts(
        build_healthy_service_metrics(), build_healthy_model_metrics(), THRESHOLDS
    )


def test_error_rate_violation_is_collected():
    service_metrics = build_healthy_service_metrics() | {"error_rate": 0.1}
    violations = collect_alert_violations(
        service_metrics, build_healthy_model_metrics(), THRESHOLDS
    )
    assert len(violations) == 1
    assert "error_rate=0.1 exceeds maximum 0.05" in violations[0]


def test_mean_probability_outside_band_is_collected():
    model_metrics = build_healthy_model_metrics() | {"mean_probability": 0.7}
    violations = collect_alert_violations(
        build_healthy_service_metrics(), model_metrics, THRESHOLDS
    )
    assert len(violations) == 1
    assert "mean_probability=0.7 is outside [0.15, 0.55]" in violations[0]


def test_enforce_raises_listing_every_violation():
    service_metrics = {"error_rate": 0.2, "latency_ms_p95": 900.0}
    with pytest.raises(ValueError, match="monitoring alerts fired") as raised:
        enforce_monitoring_alerts(service_metrics, build_healthy_model_metrics(), THRESHOLDS)
    assert "error_rate" in str(raised.value)
    assert "latency_ms_p95" in str(raised.value)
