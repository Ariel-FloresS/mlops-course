# lessons

One self-contained folder per lesson, named `NN-short-name`, each following the template defined in the root [README](../README.md).

Lessons are generated incrementally — see the roadmap in the root README for status.

- [`01-churn-ci-cd/`](01-churn-ci-cd/README.md) — churn training pipeline + local FastAPI deployment + GitHub Actions CI with a metric gate.
- [`02-monitoring/`](02-monitoring/README.md) — structured logging, service + model metrics, dashboard report, threshold alerts, scheduled monitoring workflow.
- [`03-drift-detection/`](03-drift-detection/README.md) — PSI from scratch, reference profiles, drift gate, and the drift → `repository_dispatch` → retraining chain (pipeline form 4).
- [`04-docker-lambda/`](04-docker-lambda/README.md) — Lambda container image with the model baked in, RIE local validation, OIDC credentials, and the Docker → ECR → Lambda → API Gateway deploy pipeline.
- [`05-deployment-strategies/`](05-deployment-strategies/README.md) — blue-green / canary / shadow routing service, shadow comparison of paired predictions, promotion gate, and the progressive-deploy pipeline (rollback by abstention).

Next to land here: `06-mlflow/`.

Run `pytest` from inside a lesson folder (each lesson ships its own `pytest.ini`); lessons are independent and their `src/` packages are not importable across lessons.
