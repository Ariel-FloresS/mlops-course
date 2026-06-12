import pytest

from src.deployment.promotion_gate import (
    PromotionThresholds,
    collect_promotion_blockers,
    enforce_promotion_gate,
)

THRESHOLDS = PromotionThresholds(
    min_label_agreement_rate=0.9,
    max_mean_probability_delta=0.1,
    min_comparison_count=150,
)


def build_healthy_metrics() -> dict:
    return {
        "comparison_count": 192,
        "label_agreement_rate": 0.95,
        "mean_probability_delta": 0.03,
    }


def test_healthy_comparison_passes():
    assert collect_promotion_blockers(build_healthy_metrics(), THRESHOLDS) == []
    enforce_promotion_gate(build_healthy_metrics(), THRESHOLDS)


def test_low_agreement_blocks_promotion():
    metrics = build_healthy_metrics() | {"label_agreement_rate": 0.8}
    with pytest.raises(ValueError, match="promotion blocked"):
        enforce_promotion_gate(metrics, THRESHOLDS)


def test_insufficient_samples_block_promotion():
    metrics = build_healthy_metrics() | {"comparison_count": 10}
    blockers = collect_promotion_blockers(metrics, THRESHOLDS)
    assert len(blockers) == 1
    assert "comparison_count=10 is below minimum 150" in blockers[0]


def test_every_blocker_is_listed():
    metrics = {
        "comparison_count": 10,
        "label_agreement_rate": 0.5,
        "mean_probability_delta": 0.4,
    }
    with pytest.raises(ValueError) as raised:
        enforce_promotion_gate(metrics, THRESHOLDS)
    message = str(raised.value)
    assert "comparison_count" in message
    assert "label_agreement_rate" in message
    assert "mean_probability_delta" in message
