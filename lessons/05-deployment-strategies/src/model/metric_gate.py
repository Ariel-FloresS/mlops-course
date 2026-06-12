def enforce_metric_gate(
    metrics: dict[str, float], gate_metric_name: str, minimum_value: float
) -> None:
    if gate_metric_name not in metrics:
        raise ValueError(
            f"gate metric {gate_metric_name} not in metrics: {sorted(metrics)}"
        )
    observed_value = metrics[gate_metric_name]
    if observed_value < minimum_value:
        raise ValueError(
            f"metric gate failed: {gate_metric_name}={observed_value} is below minimum {minimum_value}"
        )
