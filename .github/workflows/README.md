# workflows

GitHub Actions pipelines, added lesson by lesson.

- `01-churn-ci.yml` — Lesson 01: `test → train (metric gate, publishes churn-model artifact) → smoke-test`. Push/PR triggered with `paths:` filters; also runnable via `workflow_dispatch`.
- `02-monitoring.yml` — Lesson 02: `test → monitor (train, serve, replay traffic, aggregate, report, alerts)`. Daily cron at 06:00 UTC on `main`, plus PR and manual triggers; the monitoring-report artifact uploads even on red runs (`if: always()`).
