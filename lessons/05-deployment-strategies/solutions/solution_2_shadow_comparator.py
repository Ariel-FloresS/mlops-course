def compare_shadow_records(shadow_records: list[dict]) -> dict:
    if not shadow_records:
        raise ValueError("shadow_records must not be empty")
    comparison_count = len(shadow_records)
    agreement_count = sum(
        1 for record in shadow_records if record["blue_label"] == record["green_label"]
    )
    probability_deltas = [
        abs(record["green_probability"] - record["blue_probability"])
        for record in shadow_records
    ]
    return {
        "comparison_count": comparison_count,
        "label_agreement_rate": round(agreement_count / comparison_count, 4),
        "disagreement_count": comparison_count - agreement_count,
        "mean_probability_delta": round(sum(probability_deltas) / comparison_count, 4),
        "max_probability_delta": round(max(probability_deltas), 4),
    }
