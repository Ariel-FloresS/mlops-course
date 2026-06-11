# Exercises — Lesson 02

Four skeletons, same validation loop as Lesson 01: implement, swap into `src/`, run the matching tests, restore with git, compare with `../solutions/`.

All commands run from `lessons/02-monitoring/`.

| # | Skeleton | Replaces | Validate with | Expected |
|---|----------|----------|---------------|----------|
| 1 | `exercise_1_logging_app.py` | `src/serving/app.py` | `uv run pytest tests/test_logging_endpoints.py -q` | `3 passed` |
| 2 | `exercise_2_service_metrics.py` | `src/monitoring/service_metrics.py` | `uv run pytest tests/test_service_metrics.py -q` | `3 passed` |
| 3 | `exercise_3_alerts.py` | `src/monitoring/alerts.py` | `uv run pytest tests/test_alerts.py -q` | `4 passed` |

Example, exercise 2:

```bash
cp exercises/exercise_2_service_metrics.py src/monitoring/service_metrics.py
uv run pytest tests/test_service_metrics.py -q
git checkout -- src/monitoring/service_metrics.py
```

End-to-end check for exercises 1–3: with your implementations in place, rerun walkthrough steps 4–7. The monitoring pipeline over the canonical logs must reproduce `expected_outputs/monitoring_report.txt` byte for byte:

```bash
uv run python -m src.pipeline.monitoring_pipeline expected_outputs/requests_log_sample.jsonl expected_outputs/predictions_log_sample.jsonl
diff reports/monitoring_report.txt expected_outputs/monitoring_report.txt
```

An empty diff is a pass.

## Exercise 4 — the scheduled workflow

`exercise_4_workflow.yml` has the triggers and the whole `monitor` job removed.

1. Fill in the TODOs without looking at `.github/workflows/02-monitoring.yml`.
2. Diff against `../solutions/solution_4_workflow.yml`.
3. Real validation: copy it over `.github/workflows/02-monitoring.yml`, push a branch, open a pull request, and compare the run with `expected_outputs/workflow_run_summary.txt` (then restore the file).

Two trigger questions to answer from memory while you are at it (answers in the lesson README, section 2.5): on which branch does a `schedule` trigger run? Is the cron time guaranteed?
