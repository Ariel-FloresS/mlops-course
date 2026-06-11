# Exercises — Lesson 01

Four skeletons, ordered by increasing scope. The TODO comments inside each file are the spec; the lesson README sections 2 and 4 contain everything you need to fill them.

## The validation loop

Exercises 1–3 are drop-in replacements for reference modules, so the lesson's own test suite validates your implementation:

1. Implement the skeleton in this folder.
2. Copy it over the reference module it replaces (git is your backup).
3. Run the matching test file and compare with the expected result below.
4. Restore the reference: `git checkout -- <replaced file>`.
5. Compare your code against the matching file in `../solutions/`.

All commands run from `lessons/01-churn-ci-cd/`.

| # | Skeleton | Replaces | Validate with | Expected |
|---|----------|----------|---------------|----------|
| 1 | `exercise_1_schema_validator.py` | `src/data/schema_validator.py` | `uv run pytest tests/test_schema_validator.py -q` | `5 passed` |
| 2 | `exercise_2_metric_gate.py` | `src/model/metric_gate.py` | `uv run pytest tests/test_metric_gate.py -q` | `3 passed` |
| 3 | `exercise_3_predict_endpoint.py` | `src/serving/app.py` | `uv run pytest tests/test_predict_endpoint.py -q` | `3 passed` |

Example, exercise 1:

```bash
cp exercises/exercise_1_schema_validator.py src/data/schema_validator.py
uv run pytest tests/test_schema_validator.py -q
git checkout -- src/data/schema_validator.py
```

A full-pipeline check also works for exercises 1–2: `uv run python -m src.pipeline.train_pipeline` must reproduce `expected_outputs/train_log.txt` exactly.

## Exercise 4 — the workflow

`exercise_4_workflow.yml` is the pipeline definition with the triggers, job dependencies, and artifact steps removed.

Validation is by comparison and by execution:

1. Fill in the TODOs without looking at `.github/workflows/01-churn-ci.yml`.
2. Diff against `../solutions/solution_4_workflow.yml`.
3. Real validation: copy your version over `.github/workflows/01-churn-ci.yml`, push a branch, open a pull request, and check the run matches `expected_outputs/workflow_run_summary.txt` (then restore the file).
