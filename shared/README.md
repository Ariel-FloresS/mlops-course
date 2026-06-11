# shared

Common utilities and synthetic data generators used across lessons. Code here follows the same standards as everything else in the course (see `00-setup/README.md`, section 9).

- `churn_data.py` — deterministic synthetic churn data: `generate_churn_frame(row_count, seed)` and the `compute_churn_logit` formula that defines the label. Same seed ⇒ byte-identical output, so every learner can validate against committed expected outputs.
- `generate_churn_dataset.py` — CLI entry that writes the canonical 2,000-row, seed-42 dataset. Run from the repo root:

```bash
uv run python -m shared.generate_churn_dataset lessons/01-churn-ci-cd/data/churn.csv
```

Expected output:

```
wrote 2000 rows to lessons/01-churn-ci-cd/data/churn.csv
```
