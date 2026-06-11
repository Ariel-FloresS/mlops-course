# 02 — Monitoring: Service Metrics, Model Metrics, Logging, Dashboard

Lesson 01 ended with a model serving predictions — and total silence. You cannot tell whether it is slow, erroring, or quietly drifting into nonsense. This lesson builds the observation system: **structured logging** at the serving boundary, an **aggregation pipeline** that turns logs into service metrics and model metrics, a **report/dashboard**, **threshold alerts** that reuse the gate pattern, and a **scheduled GitHub Actions workflow** (pipeline form 3 from Lesson 00) that runs the whole loop daily.

Everything still runs without real users: a deterministic traffic replayer simulates production load, so your numbers match the expected outputs.

---

## 1. Objectives

After this lesson you can:

- Explain the difference between service metrics and model metrics, and why model metrics need proxies while true labels haven't arrived.
- Instrument a FastAPI service with two structured log streams — request-level (middleware) and prediction-level (endpoint) — without touching business logic.
- Build an aggregation pipeline: JSONL logs → windowed metrics → text/HTML report → threshold alerts.
- Recognize that an alert is the same `if/raise` gate from Lesson 01, pointed at production behavior instead of training metrics.
- Write a `schedule`-triggered workflow and state its two gotchas (default branch only, best-effort timing).
- Reproduce the full loop by hand and validate byte-exactly against canonical logs.

---

## 2. Theory

### 2.1 Deployed is not done

A live model fails in ways CI can never catch, because CI sees code and training data — not production behavior:

- **Service failures**: latency creep, error spikes, dead process. The model is fine; nobody can reach it.
- **Model failures without errors**: the service returns 200s all day while predictions go wrong — inputs shifted, an upstream system changed a unit, a category went stale. Nothing crashes. This is the dangerous one.

The catch: churn labels arrive weeks later (you learn who churned next month). So day-to-day model monitoring runs on **proxy metrics** — properties of the *predictions themselves*: their volume, mean probability, distribution shape, positive rate. If those move, something upstream moved. Confirming *what* moved is drift detection — Lesson 03 — and it will consume exactly the logs this lesson produces.

### 2.2 Service metrics vs model metrics

Two views of one running system, computed from two different log streams:

| | Service metrics | Model metrics |
|---|---|---|
| Question | "Is the service healthy?" | "Does the model still behave as expected?" |
| Source | request log (every request, incl. failures) | prediction log (successful predictions only) |
| Examples | request_count, error_rate, latency p50/p95/p99 | prediction_count, positive_rate, mean_probability, probability histogram |
| Classic framing | golden signals (traffic, errors, latency, saturation) | prediction distribution awareness |
| Breaks when | infra/code problems | data/world problems |

Latency lives in **percentiles**, not averages: an average hides the slow tail your users actually feel. p50 is the typical request, p95/p99 are the tail. Error rate counts every response with status ≥ 400 — including the 422s your own schema validation produces: a spike in 422s means *clients* started sending garbage, which is information.

### 2.3 Structured logging is the substrate

Everything downstream — metrics, dashboards, alerts, drift detection — is derived from logs. Decisions that matter:

- **JSON Lines** (one JSON object per line, append-only). Machine-parseable, streamable, no parsing heuristics. Pretty logs are for humans; production logs are for pipelines.
- **Two streams, two granularities.** The request log is written by **middleware** — it wraps every request, including ones rejected before the endpoint runs (422s never reach endpoint code, so endpoint-level logging would miss them — run the test that proves it). The prediction log is written by the **endpoint** — only it knows features and outputs.
- **Log the inputs.** Each prediction record carries the full feature payload. That feels redundant today; it is the raw material for drift detection tomorrow. (Real systems mind PII here — synthetic data spares us, the concern transfers.)
- **The logger is injected.** `create_application(model_path, request_logger, prediction_logger)` — tests pass loggers pointed at tmp files and assert on log *content*, the same dependency-injection move as the classifier in Lesson 01.

One pragmatic simplification, named honestly: we aggregate over whole log files; production systems window by time and rotate files. The metrics functions don't care — records in, metrics out.

### 2.4 Aggregate → report → alert (in that order)

The monitoring pipeline is a composition root, same role as `train_pipeline`:

```
read logs → compute service metrics → compute model metrics → write reports → enforce alerts
```

Alerts are Lesson 01's gate, re-aimed: `collect_alert_violations` (pure, returns a list of human-readable strings — testable) and `enforce_monitoring_alerts` (raises `ValueError` listing every violation — the exit-code-1 mechanism CI understands). Thresholds are config, not logic: error rate ≤ 0.05, latency p95 ≤ 500ms, prediction volume ≥ 150, mean probability inside [0.15, 0.55] — that band is the "proxy" idea concretized: the model was trained on a world where mean churn probability sits around 0.3; if live traffic averages 0.7, the world changed even though every request returned 200.

Ordering detail that separates juniors from operators: **reports are written before alerts are enforced**. A monitoring run that fails must leave behind the report explaining why. The workflow mirrors this with `if: always()` on the artifact upload.

### 2.5 Scheduled pipelines: form 3, with its gotchas

The workflow trigger is `schedule: cron: "0 6 * * *"` — pipeline form 3 from Lesson 00: automated cadence, blind to need. Honest assessment built into the design:

- It monitors **daily**, so it catches slow decay; a sudden 10:00 incident waits until tomorrow 06:00. Real systems pair scheduled checks with always-on alerting; Lesson 03 adds the event-driven half.
- **Gotcha 1**: `schedule` runs only on the **default branch** (`main`). A cron in a PR branch does nothing until merged. The workflow also has `pull_request` + `workflow_dispatch` triggers precisely so you can see it run before merge.
- **Gotcha 2**: cron times are **best effort** (queued, sometimes minutes late, occasionally skipped at peak) — fine for monitoring cadence, not for SLA-grade scheduling.

Since there is no live traffic in CI either, the workflow rebuilds the loop end to end: train → serve → **replay canonical traffic** → aggregate → report → alert. The traffic replayer sends 200 deterministic requests (`data/traffic.csv`, seed 7 — same feature distribution as training, that's the healthy baseline) and deliberately corrupts every 25th request to exercise the error path: 192 accepted, 8 rejected, error rate 0.0398 — under the 0.05 threshold by design, so you see errors *tracked* without alerts *firing*.

---

## 3. Diagrams

### 3.1 The monitoring data flow

```
                    SERVING PROCESS (run_server)
client ──► uvicorn ──► middleware ─────────────► endpoint /predict
                          │                            │
                          │ EVERY request              │ successful predictions only
                          │ (200s, 404s, 422s)         │ features + probability + label
                          ▼                            ▼
                   logs/requests.jsonl          logs/predictions.jsonl
                          │                            │
                          └──────────┬─────────────────┘
                                     │  (later, offline)
                                     ▼
                    MONITORING PIPELINE (monitoring_pipeline)
                read logs ──► service metrics ──► reports/monitoring_report.txt
                          └─► model metrics  ──►  reports/monitoring_report.html
                                     │
                                     ▼
                          enforce alerts (if/raise)
                          pass ──► exit 0, green job
                          fail ──► ValueError, exit 1, red job
                                   (reports already written)
```

### 3.2 Who writes which log, and why it matters

```
            ┌──────────────────────────────────────────────────────┐
            │                    middleware                        │
            │  sees: method, path, status, latency                 │
            │  writes: requests.jsonl  (the SERVICE view)          │
            │                                                      │
            │   ┌───────────────────────────────────────────┐      │
   request ─┼──►│  pydantic validation                      │      │
            │   │  422 ──► response (endpoint NEVER runs,   │      │
            │   │          prediction log NEVER written)    │      │
            │   │   │ valid                                 │      │
            │   │   ▼                                       │      │
            │   │  endpoint /predict                        │      │
            │   │  sees: features, probability, label       │      │
            │   │  writes: predictions.jsonl (MODEL view)   │      │
            │   └───────────────────────────────────────────┘      │
            └──────────────────────────────────────────────────────┘

  requests.jsonl  : 201 records = 1 health + 192 predictions + 8 rejections
  predictions.jsonl: 192 records
```

### 3.3 The scheduled workflow

```
cron 06:00 UTC (main only) / pull request / manual button
        │
        ▼
┌──────────────┐  green   ┌─────────────────────────────────────────┐
│ job: test    │ ───────► │ job: monitor                            │
│  pytest -q   │  needs   │  1. train          (artifact to serve)  │
│  (16 passed) │          │  2. serve + replay (populate logs)      │
└──────────────┘          │  3. monitoring pipeline                 │
                          │       reports ──► alerts (gate)         │
                          │  4. upload monitoring-report            │
                          │     if: always() ◄── report survives    │
                          └─────────────────────────────────────────┘
```

---

## 4. Walkthrough

All commands run from `lessons/02-monitoring/` unless stated otherwise. No new dependencies — monitoring is built from what Lesson 01 installed plus the standard library (`uv sync` output unchanged).

### Step 1 — inspect the traffic dataset

```bash
head -n 4 data/traffic.csv
wc -l data/traffic.csv
```

Expected output (exact — `expected_outputs/traffic_head.txt`):

```
tenure_months,monthly_charges,total_charges,contract_type,payment_method,support_tickets
69,116.71,8052.99,one_year,bank_transfer,3
46,85.78,3945.88,month_to_month,electronic_check,1
50,62.82,3141.0,one_year,electronic_check,2
```

```
201 data/traffic.csv
```

Same columns as training minus `churn` — traffic has no labels; that is the entire monitoring problem. Optional determinism check, from the **repo root**: `uv run python -m shared.generate_traffic_dataset lessons/02-monitoring/data/traffic.csv` then `git status --short` → clean.

### Step 2 — run the tests

```bash
uv run pytest -q
```

Expected output:

```
................                                                         [100%]
16 passed in 1.55s
```

### Step 3 — train (and witness cross-lesson determinism)

```bash
uv run python -m src.pipeline.train_pipeline
```

Expected output: **identical to Lesson 01**, down to `roc_auc: 0.9222` — same generator, same seed, same locked versions, same platform code. Reproducibility is transitive.

### Step 4 — serve with logging and replay production traffic

Terminal 1:

```bash
uv run python -m src.serving.run_server
```

Terminal 2 — one health check, then 200 replayed requests:

```bash
curl -fsS http://127.0.0.1:8000/health
uv run python -m src.monitoring.traffic_replay
```

Expected output (exact):

```
{"status":"ok"}
sent 200 requests: 192 accepted, 8 rejected
```

Inspect what accumulated (server can keep running or be stopped now):

```bash
wc -l logs/requests.jsonl logs/predictions.jsonl
head -n 2 logs/requests.jsonl
head -n 1 logs/predictions.jsonl
```

Expected output (counts exact; timestamps/latencies are yours):

```
  201 logs/requests.jsonl
  192 logs/predictions.jsonl
  393 total
```

```
{"latency_ms": 2.4, "method": "GET", "path": "/health", "status_code": 200, "timestamp": "2026-06-11T14:11:56.374592+00:00"}
{"latency_ms": 17.74, "method": "POST", "path": "/predict", "status_code": 200, "timestamp": "2026-06-11T14:11:56.988752+00:00"}
```

```
{"churn_label": 0, "churn_probability": 0.0076, "contract_type": "one_year", "monthly_charges": 116.71, "payment_method": "bank_transfer", "support_tickets": 3, "tenure_months": 69, "timestamp": "2026-06-11T14:11:56.987895+00:00", "total_charges": 8052.99}
```

Note the first prediction record: it is row 1 of `traffic.csv` plus the model's answer. Inputs logged with outputs — Lesson 03 will thank you.

### Step 5 — aggregate your live logs

```bash
uv run python -m src.pipeline.monitoring_pipeline
```

Expected output **shape** (counts and probability fields exact, latency fields vary — they are your machine's):

```
read 201 request records and 192 prediction records
service metrics: {'request_count': 201, 'error_count': 8, 'error_rate': 0.0398, 'latency_ms_p50': ..., 'latency_ms_p95': ..., 'latency_ms_p99': ...}
model metrics: {'prediction_count': 192, 'positive_rate': 0.2396, 'mean_probability': 0.2828, 'min_probability': 0.0011, 'max_probability': 0.9929, 'probability_buckets': [81, 30, 16, 10, 9, 8, 10, 4, 11, 13]}
reports written to reports/
all monitoring alerts passed
```

Open `reports/monitoring_report.html` in a browser — that is the dashboard. Why are model-metric values exact while latencies are not? Because predictions are a pure function of (artifact, request) and both are pinned; latency is physics.

### Step 6 — byte-exact validation against the canonical logs

`expected_outputs/` ships frozen logs from the reference run (201 + 192 records, latencies included). The pipeline accepts log-path overrides precisely for this:

```bash
uv run python -m src.pipeline.monitoring_pipeline expected_outputs/requests_log_sample.jsonl expected_outputs/predictions_log_sample.jsonl
diff reports/monitoring_report.txt expected_outputs/monitoring_report.txt
diff reports/monitoring_report.html expected_outputs/monitoring_report.html
```

Expected: stdout matches `expected_outputs/monitoring_pipeline_log.txt` exactly (p50 4.71 / p95 6.8 / p99 7.66), and **both diffs are empty**. The report includes the text dashboard:

```
PREDICTION PROBABILITY DISTRIBUTION
  0.0-0.1 | ######################################## 81
  0.1-0.2 | ############### 30
  0.2-0.3 | ######## 16
  0.3-0.4 | ##### 10
  0.4-0.5 | #### 9
  0.5-0.6 | #### 8
  0.6-0.7 | ##### 10
  0.7-0.8 | ## 4
  0.8-0.9 | ##### 11
  0.9-1.0 | ###### 13
```

Heavy left mass (low churn probabilities), thin right tail — memorize this shape. Lesson 03 is the story of this histogram changing while every request still returns 200.

### Step 7 — fire an alert on purpose

Strict thresholds injected over the same canonical logs (`error_rate` max squeezed to 0.01):

```bash
uv run python -c "
from dataclasses import replace
from pathlib import Path
from src.monitoring.alerts import MonitoringThresholds
from src.pipeline.config import DEFAULT_MONITORING_CONFIG
from src.pipeline.monitoring_pipeline import run_monitoring_pipeline
strict_thresholds = MonitoringThresholds(
    max_error_rate=0.01,
    max_latency_ms_p95=500.0,
    min_prediction_count=150,
    min_mean_probability=0.15,
    max_mean_probability=0.55,
)
run_monitoring_pipeline(
    replace(
        DEFAULT_MONITORING_CONFIG,
        request_log_path=Path('expected_outputs/requests_log_sample.jsonl'),
        prediction_log_path=Path('expected_outputs/predictions_log_sample.jsonl'),
        thresholds=strict_thresholds,
    )
)
"
echo "exit code: $?"
```

Expected: metrics and `reports written to reports/` print first, then a traceback ending in (`expected_outputs/alert_failure_log.txt`):

```
ValueError: monitoring alerts fired: ['error_rate=0.0398 exceeds maximum 0.01']
exit code: 1
```

Same mechanism as the metric gate — and the report was written *before* the alert killed the run.

### Step 8 — read the scheduled workflow, then watch it

Open `.github/workflows/02-monitoring.yml`:

- `schedule: cron "0 6 * * *"` — daily 06:00 UTC, **default branch only, best effort** (§2.5).
- `pull_request` + `workflow_dispatch` — so the pipeline is visible before merge and runnable on demand.
- Job `monitor` (`needs: test`) replays this exact walkthrough: train → serve+replay → aggregate → alert.
- `if: always()` on the upload — the monitoring-report artifact survives red runs.

Push or open a PR touching this lesson and compare the run with `expected_outputs/workflow_run_summary.txt`.

---

## 5. Expected outputs — file map

| File | Produced by | Varies between machines |
|---|---|---|
| `traffic_head.txt` | `head -n 4 data/traffic.csv` | nothing |
| `pytest_output.txt` | `uv run pytest -q` | duration |
| `train_log.txt` | training (step 3) | nothing — identical to Lesson 01 |
| `server_startup_log.txt` | `run_server` | pid |
| `traffic_replay_output.txt` | `traffic_replay` (step 4) | nothing |
| `requests_log_sample.jsonl` | canonical frozen request log (201 records) | n/a — committed reference |
| `predictions_log_sample.jsonl` | canonical frozen prediction log (192 records) | n/a — committed reference |
| `monitoring_pipeline_log.txt` | pipeline over canonical logs (step 6) | nothing |
| `monitoring_report.txt` / `.html` | pipeline over canonical logs (step 6) | nothing — diff must be empty |
| `alert_failure_log.txt` | step 7 | absolute paths in traceback |
| `workflow_run_summary.txt` | reading the Actions run | timings, ± health retries |

On **live** logs (steps 4–5): counts and probability-derived values are exact, latency-derived values are not. Knowing *which* fields are deterministic is itself a monitoring skill.

---

## 6. Exercises

Skeletons in `exercises/`, answers in `solutions/`, loop described in `exercises/README.md`.

1. **Logging app** (`exercise_1_logging_app.py`) — implement the record builders, the timing middleware, and the prediction-log write. Valid: `uv run pytest tests/test_logging_endpoints.py -q` → `3 passed`.
2. **Service metrics** (`exercise_2_service_metrics.py`) — counts, error rate, latency percentiles. Valid: `3 passed`.
3. **Alerts** (`exercise_3_alerts.py`) — `collect_alert_violations` + `enforce_monitoring_alerts`, every threshold, all violations listed. Valid: `4 passed`.
4. **Scheduled workflow** (`exercise_4_workflow.yml`) — rebuild triggers and the `monitor` job from memory; validate by diff or by a real PR run.

Final boss for 1–3 combined: the byte-exact diff of step 6 with your implementations swapped in.

---

## 7. Validation checklist

- [ ] `uv run pytest -q` prints `16 passed`.
- [ ] Replay prints exactly `sent 200 requests: 192 accepted, 8 rejected`; logs hold 201/192 lines.
- [ ] I can say which log stream the middleware writes, which the endpoint writes, and why a 422 appears in one but not the other.
- [ ] Pipeline over canonical logs reproduces `monitoring_report.txt` with an **empty diff**.
- [ ] Step 7 prints `exit code: 1` *after* `reports written to reports/` — and I can say why that ordering is deliberate.
- [ ] I can name the four alert thresholds and what real-world failure each one catches.
- [ ] I can state the two `schedule` gotchas (default branch only; best-effort timing) and what `if: always()` protects.
- [ ] I can explain why mean_probability is a *proxy* metric and what it is a proxy for.

---

## 8. Build from scratch

Rebuild order, each stage with a checkable "done". Keep `data/`, `tests/`, and the canonical logs as your harness; the platform layers (`data/features/model` + `train_pipeline`) carry over from your Lesson 01 rebuild.

1. **`serving/json_lines_logger.py`** — done: `pytest tests/test_json_lines_logger.py` → `3 passed`.
2. **`serving/app.py` extension** — record builders, middleware, endpoint write, logger injection. Done: `pytest tests/test_logging_endpoints.py` → `3 passed`.
3. **`serving/run_server.py`** — wire both loggers. Done: manual curl produces one line in each log.
4. **`monitoring/log_reader.py`** — done: reading a canonical sample returns 201 records; a missing path raises.
5. **`monitoring/service_metrics.py`** — done: `3 passed`.
6. **`monitoring/model_metrics.py`** — done: `3 passed`.
7. **`monitoring/alerts.py`** — done: `4 passed`.
8. **`monitoring/report.py`** — done: rendering the canonical metrics reproduces `monitoring_report.txt` byte for byte.
9. **`pipeline/config.py` + `pipeline/monitoring_pipeline.py`** — done: step 6 diffs are empty; step 7 exits 1.
10. **`monitoring/traffic_replay.py`** — done: against a running server, prints the exact replay line and the logs gain 200/192 records.
11. **`.github/workflows/02-monitoring.yml`** — done: PR run matches `workflow_run_summary.txt`.

Same rule as Lesson 01: when stuck, the failing test and the expected output are the spec — not `src/`.

---

## Lesson summary

- Monitoring is two log streams written at the serving boundary — middleware logs every request (service view), the endpoint logs every prediction with its inputs (model view) — and everything downstream is derived from them.
- The monitoring pipeline is a composition root that turns logs into service + model metrics, writes the report *first*, then enforces threshold alerts with the same `if/raise → exit 1` gate that protects training.
- A `schedule` cron makes it pipeline form 3 — automated cadence, default-branch only, best effort — with proxy model metrics (volume, mean probability, distribution) standing in for labels that haven't arrived yet.

**Next — Lesson 03 (Drift detection):** the probability histogram you memorized starts moving. You'll detect data drift (inputs shifted) and concept drift (the input→label relationship shifted), quantify them with statistical distances, and wire detection to an automated retraining trigger — pipeline form 4, the event-driven half that the daily cron can't cover.
