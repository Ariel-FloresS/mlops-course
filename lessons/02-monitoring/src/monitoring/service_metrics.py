import numpy as np


def compute_service_metrics(request_records: list[dict]) -> dict[str, float | int]:
    if not request_records:
        raise ValueError("request_records must not be empty")
    status_codes = [record["status_code"] for record in request_records]
    latencies_ms = [record["latency_ms"] for record in request_records]
    request_count = len(request_records)
    error_count = sum(1 for status_code in status_codes if status_code >= 400)
    return {
        "request_count": request_count,
        "error_count": error_count,
        "error_rate": round(error_count / request_count, 4),
        "latency_ms_p50": round(float(np.percentile(latencies_ms, 50)), 2),
        "latency_ms_p95": round(float(np.percentile(latencies_ms, 95)), 2),
        "latency_ms_p99": round(float(np.percentile(latencies_ms, 99)), 2),
    }
