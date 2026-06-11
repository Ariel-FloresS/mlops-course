import pytest

from src.monitoring.service_metrics import compute_service_metrics


def build_record(status_code: int, latency_ms: float) -> dict:
    return {"status_code": status_code, "latency_ms": latency_ms}


def test_counts_and_error_rate():
    records = [
        build_record(200, 10.0),
        build_record(200, 20.0),
        build_record(200, 30.0),
        build_record(422, 40.0),
    ]
    metrics = compute_service_metrics(records)
    assert metrics["request_count"] == 4
    assert metrics["error_count"] == 1
    assert metrics["error_rate"] == 0.25
    assert metrics["latency_ms_p50"] == 25.0


def test_latency_percentiles_with_linear_interpolation():
    records = [build_record(200, float(value)) for value in range(10, 101, 10)]
    metrics = compute_service_metrics(records)
    assert metrics["latency_ms_p50"] == 55.0
    assert metrics["latency_ms_p95"] == 95.5
    assert metrics["latency_ms_p99"] == 99.1


def test_rejects_empty_records():
    with pytest.raises(ValueError, match="must not be empty"):
        compute_service_metrics([])
