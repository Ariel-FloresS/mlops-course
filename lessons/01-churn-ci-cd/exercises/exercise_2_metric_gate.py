def enforce_metric_gate(
    metrics: dict[str, float], gate_metric_name: str, minimum_value: float
) -> None:
    # TODO: raise ValueError containing "not in metrics" if gate_metric_name
    #       is not a key of metrics
    # TODO: read the observed value for gate_metric_name
    # TODO: raise ValueError containing "metric gate failed" (and stating the
    #       observed value and the minimum) if the observed value is BELOW the minimum
    # NOTE: a value exactly equal to the minimum must pass
    raise NotImplementedError
