import pytest

from src.monitoring.model_metrics import compute_model_metrics


def build_record(churn_probability: float) -> dict:
    return {
        "churn_probability": churn_probability,
        "churn_label": int(churn_probability >= 0.5),
    }


def test_rates_and_probability_summary():
    records = [build_record(p) for p in (0.1, 0.9, 0.5, 0.7)]
    metrics = compute_model_metrics(records)
    assert metrics["prediction_count"] == 4
    assert metrics["positive_rate"] == 0.75
    assert metrics["mean_probability"] == 0.55
    assert metrics["min_probability"] == 0.1
    assert metrics["max_probability"] == 0.9


def test_probability_buckets_including_edge_values():
    records = [build_record(p) for p in (0.05, 0.15, 0.95, 1.0, 0.99)]
    metrics = compute_model_metrics(records)
    assert metrics["probability_buckets"] == [1, 1, 0, 0, 0, 0, 0, 0, 0, 3]


def test_rejects_empty_records():
    with pytest.raises(ValueError, match="must not be empty"):
        compute_model_metrics([])
