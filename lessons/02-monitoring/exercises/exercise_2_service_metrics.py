import numpy as np


def compute_service_metrics(request_records: list[dict]) -> dict[str, float | int]:
    # TODO: raise ValueError if request_records is empty
    # TODO: extract status_code and latency_ms from every record
    # TODO: count errors (status_code >= 400)
    # TODO: return a dict with request_count, error_count,
    #       error_rate (rounded to 4 decimals),
    #       latency_ms_p50 / latency_ms_p95 / latency_ms_p99
    #       (np.percentile, rounded to 2 decimals)
    raise NotImplementedError
