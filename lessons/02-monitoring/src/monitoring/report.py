SERVICE_METRIC_NAMES = (
    "request_count",
    "error_count",
    "error_rate",
    "latency_ms_p50",
    "latency_ms_p95",
    "latency_ms_p99",
)
MODEL_METRIC_NAMES = (
    "prediction_count",
    "positive_rate",
    "mean_probability",
    "min_probability",
    "max_probability",
)
BAR_MAX_WIDTH = 40


def render_probability_bars(bucket_counts: list[int]) -> list[str]:
    if len(bucket_counts) != 10:
        raise ValueError(f"expected 10 probability buckets, got {len(bucket_counts)}")
    max_count = max(bucket_counts)
    lines = []
    for bucket_index, count in enumerate(bucket_counts):
        lower_bound = bucket_index / 10
        upper_bound = (bucket_index + 1) / 10
        bar = "#" * round(count * BAR_MAX_WIDTH / max_count)
        lines.append(f"  {lower_bound:.1f}-{upper_bound:.1f} | {bar} {count}")
    return lines


def render_text_report(service_metrics: dict, model_metrics: dict) -> str:
    lines = [
        "CHURN SERVICE MONITORING REPORT",
        "===============================",
        "",
        "SERVICE METRICS (source: requests log)",
    ]
    for metric_name in SERVICE_METRIC_NAMES:
        lines.append(f"  {metric_name:<18} {service_metrics[metric_name]}")
    lines.append("")
    lines.append("MODEL METRICS (source: predictions log)")
    for metric_name in MODEL_METRIC_NAMES:
        lines.append(f"  {metric_name:<18} {model_metrics[metric_name]}")
    lines.append("")
    lines.append("PREDICTION PROBABILITY DISTRIBUTION")
    lines.extend(render_probability_bars(model_metrics["probability_buckets"]))
    return "\n".join(lines) + "\n"


def render_metric_rows(metrics: dict, metric_names: tuple[str, ...]) -> str:
    return "".join(
        f"<tr><td>{metric_name}</td><td>{metrics[metric_name]}</td></tr>"
        for metric_name in metric_names
    )


def render_bucket_rows(bucket_counts: list[int]) -> str:
    max_count = max(bucket_counts)
    rows = []
    for bucket_index, count in enumerate(bucket_counts):
        width_percent = round(count * 100 / max_count)
        rows.append(
            f'<tr><td>{bucket_index / 10:.1f}-{(bucket_index + 1) / 10:.1f}</td>'
            f'<td><div style="background:#4a7c59;color:white;width:{width_percent}%;'
            f'min-width:fit-content;padding:2px 4px">{count}</div></td></tr>'
        )
    return "".join(rows)


def render_html_report(service_metrics: dict, model_metrics: dict) -> str:
    return (
        "<!DOCTYPE html><html><head><title>Churn Service Monitoring Report</title>"
        "<style>body{font-family:monospace;margin:2em}table{border-collapse:collapse;margin-bottom:2em}"
        "td{border:1px solid #ccc;padding:4px 12px}h2{margin-bottom:0.5em}</style></head><body>"
        "<h1>Churn Service Monitoring Report</h1>"
        "<h2>Service metrics</h2><table>"
        + render_metric_rows(service_metrics, SERVICE_METRIC_NAMES)
        + "</table><h2>Model metrics</h2><table>"
        + render_metric_rows(model_metrics, MODEL_METRIC_NAMES)
        + "</table><h2>Prediction probability distribution</h2><table>"
        + render_bucket_rows(model_metrics["probability_buckets"])
        + "</table></body></html>"
    )
