# workflows

GitHub Actions pipelines, added lesson by lesson.

- `01-churn-ci.yml` — Lesson 01: `test → train (metric gate, publishes churn-model artifact) → smoke-test`. Triggered by pushes to `main` and pull requests that touch the lesson, `shared/`, or the dependency files; also runnable manually via `workflow_dispatch`.
