# workflows

GitHub Actions pipelines, added lesson by lesson.

- `01-churn-ci.yml` — Lesson 01: `test → train (metric gate, publishes churn-model artifact) → smoke-test`. Push/PR triggered with `paths:` filters; also runnable via `workflow_dispatch`.
- `02-monitoring.yml` — Lesson 02: `test → monitor (train, serve, replay traffic, aggregate, report, alerts)`. Daily cron at 06:00 UTC on `main`, plus PR and manual triggers; the monitoring-report artifact uploads even on red runs (`if: always()`).
- `03-drift-detection.yml` — Lesson 03: `test → drift-check (train, serve, replay drifted traffic, PSI gate under continue-on-error)`; on drift it POSTs a `repository_dispatch` event `drift-detected`. Daily cron at 07:00 UTC, PR trigger, and a manual `traffic_profile` choice (drifted | baseline).
- `03-retrain-on-drift.yml` — Lesson 03: listener for `repository_dispatch: [drift-detected]` (runs from the default branch); retrains and uploads the `churn-model-retrained` artifact.
