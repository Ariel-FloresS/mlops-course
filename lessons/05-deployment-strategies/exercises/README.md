# Exercises — Lesson 05

Same loop: implement, swap into `src/`, run the matching tests, restore with git, compare with `../solutions/`.

All commands run from `lessons/05-deployment-strategies/`.

| # | Skeleton | Replaces | Validate with | Expected |
|---|----------|----------|---------------|----------|
| 1 | `exercise_1_router.py` | `src/serving/router.py` | `uv run pytest tests/test_router.py -q` | `4 passed` |
| 2 | `exercise_2_shadow_comparator.py` | `src/deployment/shadow_comparator.py` | `uv run pytest tests/test_shadow_comparator.py -q` | `3 passed` |
| 3 | `exercise_3_promotion_gate.py` | `src/deployment/promotion_gate.py` | `uv run pytest tests/test_promotion_gate.py -q` | `4 passed` |

Example, exercise 1:

```bash
cp exercises/exercise_1_router.py src/serving/router.py
uv run pytest tests/test_router.py -q
git checkout -- src/serving/router.py
```

End-to-end check for exercises 1–3 combined — the promotion pipeline over the canonical shadow log must reproduce the report byte for byte:

```bash
uv run python -m src.pipeline.promotion_pipeline expected_outputs/shadow_log_sample.jsonl
diff reports/promotion_report.txt expected_outputs/promotion_report.txt
```

Exit 0 and an empty diff is a pass.

## Exercise 4 — the progressive pipeline

`exercise_4_workflow.yml` has the triggers and all four stages removed.

1. Fill in the TODOs without looking at `.github/workflows/05-progressive-deploy.yml`.
2. Diff against `../solutions/solution_4_workflow.yml`.
3. Real validation: push a branch, open a pull request, compare the run with `expected_outputs/workflow_run_summary.txt` — including the deterministic `green assignments in first 10 requests: 2` assertion.

Question to answer from memory (answer in the lesson README, §2.4): if the promotion gate fails, what *exactly* performs the "rollback"? (Hint: nothing runs.)
