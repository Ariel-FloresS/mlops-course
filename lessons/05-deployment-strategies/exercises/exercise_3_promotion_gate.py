from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionThresholds:
    min_label_agreement_rate: float
    max_mean_probability_delta: float
    min_comparison_count: int


def collect_promotion_blockers(
    comparison_metrics: dict, thresholds: PromotionThresholds
) -> list[str]:
    # TODO: build one human-readable string per violated threshold:
    #       1. comparison_count below min_comparison_count
    #          ("comparison_count=X is below minimum Y")
    #       2. label_agreement_rate below min_label_agreement_rate
    #          ("label_agreement_rate=X is below minimum Y")
    #       3. mean_probability_delta above max_mean_probability_delta
    #          ("mean_probability_delta=X exceeds maximum Y")
    # TODO: return the list (empty means green may be promoted)
    raise NotImplementedError


def enforce_promotion_gate(
    comparison_metrics: dict, thresholds: PromotionThresholds
) -> None:
    # TODO: collect the blockers; if any exist, raise ValueError with a
    #       message starting with "promotion blocked:" listing every blocker
    raise NotImplementedError
