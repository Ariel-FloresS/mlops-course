# shared

Common utilities and synthetic data generators used across lessons. Code here follows the same standards as everything else in the course (see `00-setup/README.md`, section 9).

- `churn_data.py` — deterministic synthetic churn data: `generate_feature_columns` (the customer-feature distributions), `compute_churn_logit` (the formula that defines the label), and `generate_churn_frame(row_count, seed)`. Same seed ⇒ byte-identical output, so every learner can validate against committed expected outputs.
- `generate_churn_dataset.py` — CLI entry for the canonical 2,000-row, seed-42 **training** dataset.
- `churn_traffic.py` — `generate_traffic_frame(request_count, seed)`: unlabeled requests drawn from the same feature distributions (the monitoring/drift baseline).
- `generate_traffic_dataset.py` — CLI entry for the canonical 200-row, seed-7 **traffic** dataset.
- `churn_drifted_traffic.py` — `generate_drifted_traffic_frame(request_count, seed)`: same schema, shifted distributions (tenure 1–24, charges 60–140, 75% month-to-month, 60% electronic check, Poisson(3.0) tickets) — the deterministic "world changed" for drift detection.
- `generate_drifted_traffic_dataset.py` — CLI entry for the canonical 200-row, seed-21 **drifted** dataset.

Run from the repo root:

```bash
uv run python -m shared.generate_churn_dataset lessons/01-churn-ci-cd/data/churn.csv
uv run python -m shared.generate_traffic_dataset lessons/02-monitoring/data/traffic.csv
uv run python -m shared.generate_drifted_traffic_dataset lessons/03-drift-detection/data/traffic_drifted.csv
```

Expected outputs:

```
wrote 2000 rows to lessons/01-churn-ci-cd/data/churn.csv
wrote 200 rows to lessons/02-monitoring/data/traffic.csv
wrote 200 rows to lessons/03-drift-detection/data/traffic_drifted.csv
```
