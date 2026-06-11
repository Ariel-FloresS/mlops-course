# Exercises — Lesson 03

Same validation loop as previous lessons: implement, swap into `src/`, run the matching tests, restore with git, compare with `../solutions/`.

All commands run from `lessons/03-drift-detection/`.

| # | Skeleton | Replaces | Validate with | Expected |
|---|----------|----------|---------------|----------|
| 1 | `exercise_1_psi.py` | `src/drift/psi.py` | `uv run pytest tests/test_psi.py -q` | `4 passed` |
| 2 | `exercise_2_reference_profile.py` | `src/drift/reference_profile.py` | `uv run pytest tests/test_reference_profile.py -q` | `4 passed` |
| 3 | `exercise_3_drift_gate.py` | `src/drift/drift_gate.py` | `uv run pytest tests/test_drift_gate.py -q` | `3 passed` |

Example, exercise 1:

```bash
cp exercises/exercise_1_psi.py src/drift/psi.py
uv run pytest tests/test_psi.py -q
git checkout -- src/drift/psi.py
```

End-to-end check for exercises 1–3 combined — with your implementations in place, both canonical runs must reproduce the expected outputs exactly:

```bash
uv run python -m src.pipeline.drift_pipeline expected_outputs/predictions_log_baseline.jsonl
diff reports/drift_report.txt expected_outputs/drift_report_baseline.txt

uv run python -m src.pipeline.drift_pipeline expected_outputs/predictions_log_drifted.jsonl
diff reports/drift_report.txt expected_outputs/drift_report_drifted.txt
```

First command exits 0 with empty diff; second exits 1 (gate fired) and the diff is still empty — the report is written before the gate.

## Exercise 4 — the drift workflow with a retraining dispatch

`exercise_4_drift_workflow.yml` has the triggers and the entire signal chain removed (`continue-on-error` capture, artifact upload, `repository_dispatch` POST).

1. Fill in the TODOs without looking at `.github/workflows/03-drift-detection.yml`.
2. Diff against `../solutions/solution_4_drift_workflow.yml`.
3. Real validation: push a branch, open a pull request, and compare the runs of **both** workflows with `expected_outputs/workflow_run_summary.txt`.

Three questions to answer from memory (answers in the lesson README, sections 2.4–2.5): why `continue-on-error: true` instead of letting the job fail? Why does the dispatched retraining workflow run from the default branch? What single line prevents GitHub's "GITHUB_TOKEN events don't trigger workflows" rule from blocking this chain?
