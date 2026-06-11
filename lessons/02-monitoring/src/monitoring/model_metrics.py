def compute_model_metrics(prediction_records: list[dict]) -> dict:
    if not prediction_records:
        raise ValueError("prediction_records must not be empty")
    probabilities = [record["churn_probability"] for record in prediction_records]
    labels = [record["churn_label"] for record in prediction_records]
    bucket_counts = [0] * 10
    for probability in probabilities:
        bucket_index = min(int(probability * 10), 9)
        bucket_counts[bucket_index] += 1
    prediction_count = len(prediction_records)
    return {
        "prediction_count": prediction_count,
        "positive_rate": round(sum(labels) / prediction_count, 4),
        "mean_probability": round(sum(probabilities) / prediction_count, 4),
        "min_probability": round(min(probabilities), 4),
        "max_probability": round(max(probabilities), 4),
        "probability_buckets": bucket_counts,
    }
