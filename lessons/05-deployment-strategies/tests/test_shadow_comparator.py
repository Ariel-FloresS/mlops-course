import pytest

from src.deployment.shadow_comparator import compare_shadow_records


def build_record(blue_probability: float, green_probability: float) -> dict:
    return {
        "blue_probability": blue_probability,
        "blue_label": int(blue_probability >= 0.5),
        "green_probability": green_probability,
        "green_label": int(green_probability >= 0.5),
    }


def test_identical_predictions_agree_perfectly():
    records = [build_record(0.9, 0.9), build_record(0.1, 0.1)]
    metrics = compare_shadow_records(records)
    assert metrics["label_agreement_rate"] == 1.0
    assert metrics["disagreement_count"] == 0
    assert metrics["mean_probability_delta"] == 0.0


def test_metrics_match_hand_computation():
    records = [
        build_record(0.9, 0.8),
        build_record(0.45, 0.55),
        build_record(0.2, 0.3),
        build_record(0.7, 0.6),
    ]
    metrics = compare_shadow_records(records)
    assert metrics["comparison_count"] == 4
    assert metrics["label_agreement_rate"] == 0.75
    assert metrics["disagreement_count"] == 1
    assert metrics["mean_probability_delta"] == 0.1
    assert metrics["max_probability_delta"] == 0.1


def test_rejects_empty_records():
    with pytest.raises(ValueError, match="must not be empty"):
        compare_shadow_records([])
