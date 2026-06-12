from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionThresholds:
    min_label_agreement_rate: float
    max_mean_probability_delta: float
    min_comparison_count: int


def collect_promotion_blockers(
    comparison_metrics: dict, thresholds: PromotionThresholds
) -> list[str]:
    blockers = []
    if comparison_metrics["comparison_count"] < thresholds.min_comparison_count:
        blockers.append(
            f"comparison_count={comparison_metrics['comparison_count']} "
            f"is below minimum {thresholds.min_comparison_count}"
        )
    if comparison_metrics["label_agreement_rate"] < thresholds.min_label_agreement_rate:
        blockers.append(
            f"label_agreement_rate={comparison_metrics['label_agreement_rate']} "
            f"is below minimum {thresholds.min_label_agreement_rate}"
        )
    if comparison_metrics["mean_probability_delta"] > thresholds.max_mean_probability_delta:
        blockers.append(
            f"mean_probability_delta={comparison_metrics['mean_probability_delta']} "
            f"exceeds maximum {thresholds.max_mean_probability_delta}"
        )
    return blockers


def enforce_promotion_gate(
    comparison_metrics: dict, thresholds: PromotionThresholds
) -> None:
    blockers = collect_promotion_blockers(comparison_metrics, thresholds)
    if blockers:
        raise ValueError(f"promotion blocked: {blockers}")
