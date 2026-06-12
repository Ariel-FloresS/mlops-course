PROMOTION_METRIC_NAMES = (
    "comparison_count",
    "label_agreement_rate",
    "disagreement_count",
    "mean_probability_delta",
    "max_probability_delta",
)


def render_promotion_report(
    comparison_metrics: dict, thresholds_summary: dict[str, float | int]
) -> str:
    lines = [
        "SHADOW COMPARISON REPORT — blue (live) vs green (candidate)",
        "===========================================================",
        "",
    ]
    for metric_name in PROMOTION_METRIC_NAMES:
        lines.append(f"  {metric_name:<26} {comparison_metrics[metric_name]}")
    lines.append("")
    lines.append("promotion thresholds")
    for threshold_name, threshold_value in thresholds_summary.items():
        lines.append(f"  {threshold_name:<26} {threshold_value}")
    return "\n".join(lines) + "\n"
