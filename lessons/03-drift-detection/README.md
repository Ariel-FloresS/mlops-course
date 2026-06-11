# 03 — Drift Detection: PSI from Scratch + Automated Retraining Triggers

Lesson 02 left you watching a healthy histogram. This lesson moves it. You will quantify **data drift** with the Population Stability Index (PSI) implemented from scratch, compare live prediction logs against the training data's reference profile, and — the main event — close the loop from Lesson 00's ML diagram: **drift detected → `repository_dispatch` → retraining workflow fires by itself**. That is pipeline **form 4**, the event-driven trigger, built on top of forms 2 and 3.

The world-change is simulated honestly: a second deterministic traffic generator with shifted distributions (newer customers, higher prices, more support tickets). Same schema, same valid requests, every response still 200 — and the model is silently wrong.

---

## 1. Objectives

After this lesson you can:

- Distinguish data drift, concept drift, and label shift, and explain why input drift is detectable immediately while concept drift must wait for labels.
- Implement PSI from scratch — quantile binning, proportion vectors, the `(a−e)·ln(a/e)` formula, zero-clipping — and interpret the 0.1 / 0.2 thresholds.
- Build per-feature reference profiles from training data and score current traffic against them, using the prediction logs Lesson 02 taught you to write.
- Convert a gate failure into an automation signal: `continue-on-error` + outcome check + `repository_dispatch`, including the `GITHUB_TOKEN` and default-branch rules that make or break the chain.
- Reproduce both runs (baseline pass, drifted fire) byte-exactly against canonical logs.

---

## 2. Theory

### 2.1 Three kinds of drift

The model learned `P(churn | features)` from a snapshot of the world. Three things can move:

| Kind | What moved | Example here | Detectable from |
|---|---|---|---|
| **Data drift** (covariate shift) | the input distribution `P(features)` | customer base shifts to short-tenure, month-to-month, e-check | inputs alone — **immediately** |
| **Concept drift** | the relationship `P(churn \| features)` | a competitor launches; the same customer now churns more | needs **labels**, which arrive weeks late |
| **Label shift** | the outcome rate `P(churn)` | overall churn climbs from 28% to 45% | labels (late), hinted earlier by prediction shift |

This lesson detects **data drift**, because it is what you can catch *today*: inputs are in the prediction logs the moment they arrive. Concept drift detection is the same machinery pointed at error rates once labels land — the reason real systems also log predictions with IDs for later joining (we already log full inputs; Lesson 02's foresight pays off here).

Why care about data drift if accuracy "might" survive it? Because the model is now **extrapolating**: scoring inputs from regions it barely saw in training. Maybe predictions hold; nobody can promise it. Drift is the early-warning smoke, not the fire itself — which is exactly why the response is *retrain on fresh data*, not *page a human at 3 a.m.*

### 2.2 PSI: one number per feature

The Population Stability Index measures how far a current distribution sits from a reference distribution, over a fixed set of buckets:

```
PSI = Σ over buckets of (actual% − expected%) · ln(actual% / expected%)
```

- **expected%** — proportion of *training* data in the bucket (the reference profile).
- **actual%** — proportion of *current* traffic in the same buckets.
- Each term is ≥ 0 (a positive number times a log with the same sign), so PSI accumulates; identical distributions give exactly 0.

Buckets: **numeric features** use ~10 quantile bins computed from the reference (deciles — every bin holds ~10% of training data, so the expected vector is flat and any current pile-up is visible). **Categorical features** use the categories themselves. Zeros are clipped to `1e-4` before the log, otherwise an empty bucket explodes the formula.

Industry rules of thumb (calibrate per case, but they are the standard vocabulary):

| PSI | Reading |
|---|---|
| < 0.1 | stable |
| 0.1 – 0.2 | moderate shift, watch it |
| ≥ 0.2 | significant — act (our gate threshold) |

Why PSI over a KS test or fancier distances? It is symmetric-enough, bounded-ish in practice, works identically for numeric and categorical features, needs no p-value interpretation, and you can compute it by hand — which you will, in the tests (`compute_psi((0.5, 0.5), (0.9, 0.1)) == 0.8789`).

### 2.3 Reference profile: freeze it at training time

Drift is always *relative to what the model learned*. The reference profile — bin edges + expected proportions per feature — is derived from `data/churn.csv`, the exact frame the model trained on. The profile is the model's "memory of normal":

- numeric: inner decile edges via `np.quantile`, proportions via `searchsorted` + `bincount`;
- categorical: alphabetically-sorted value frequencies.

In this lesson the pipeline rebuilds the profile from the committed CSV on every run (cheap, deterministic). In production you would persist the profile *next to the model artifact* at training time — same idea as `metrics.json`. Lesson 06's registry gives it a proper home.

### 2.4 From red gate to automation signal

Lessons 01–02 taught one mechanism: `raise ValueError → exit 1 → red job → humans look`. Drift changes the *consumer* of that signal. A drifted feature does not need a human — it needs a retraining run. The workflow converts failure into action in three moves:

```yaml
- id: drift-check
  continue-on-error: true          # capture the exit code instead of dying
  run: uv run python -m src.pipeline.drift_pipeline

- if: steps.drift-check.outcome == 'failure'   # the captured signal
  run: curl -X POST .../dispatches -d '{"event_type": "drift-detected"}'
```

The drift gate still raises; the pipeline code knows nothing about CI (same `if/raise` as ever). The *workflow* decides what a failure means — here, "send a `repository_dispatch` event". The retraining workflow declares itself a listener:

```yaml
on:
  repository_dispatch:
    types: [drift-detected]
```

This is the **form 3 → form 4 evolution in one YAML block**: same scheduled detection, but the response is automated. Honest trade-off note: `continue-on-error` treats *any* failure of that step (even a bug) as "drift". Production systems separate signal from crash — distinct exit codes or an output file. We keep the teaching pattern minimal and name the simplification.

And the honest limitation of the demo: retraining on the **same committed CSV** produces the same model — here the dispatch chain *is* the lesson, the plumbing that form 4 requires. With a live data source, the retrain pulls fresh labeled data and the loop genuinely heals the model.

### 2.5 The three GitHub rules that make or break the chain

1. **`GITHUB_TOKEN` events do not trigger workflows** — except `workflow_dispatch` and `repository_dispatch`. That exception is the entire reason this chain works with the built-in token and no PAT. (Anything else — e.g., a bot commit — would chain nothing.)
2. **`repository_dispatch` workflows always run from the default branch.** On this lesson's first PR, the dispatch is sent into the void: the listener YAML isn't on `main` yet. After merge, the chain completes. (The drift run itself shows the dispatch step green either way.)
3. **The job needs permission to create the event**: `permissions: contents: write` on the `drift-check` job — explicit, least-privilege, visible in the YAML instead of inherited silently.

---

## 3. Diagrams

### 3.1 The drift-detection data flow

```
TRAINING TIME (the reference)              SERVING TIME (the current window)

data/churn.csv (2000 rows)                 traffic ──► /predict ──► logs/predictions.jsonl
      │                                                              (features logged per
      ▼                                                               prediction — Lesson 02)
build profiles per feature                        │
  numeric: decile bin edges                       ▼
           + expected proportions          current frame (192 records)
  categorical: category frequencies               │
      │                                           │
      └────────────────┬──────────────────────────┘
                       ▼
            compute_psi_by_feature
            one PSI per feature, same buckets
                       │
                       ▼
            reports/drift_report.txt   (written FIRST)
                       │
                       ▼
            drift gate: any psi ≥ 0.2 ?
            no  ──► exit 0, green
            yes ──► ValueError, exit 1 ──► (the workflow turns this into a signal)
```

### 3.2 Reference vs drifted, the picture worth memorizing

```
tenure_months          reference (training)        drifted traffic
  deciles of 1–72      ~10% per bin (flat)         1–24 only: everything
                                                   piles into the low bins
  bin:  1..7 │██████████ 10%                       ████████████████████ ~58%
       8..14 │██████████ 10%                       ████████████ ~33%
      15..21 │██████████ 10%                       ███ ~8%
        ...  │██████████ 10%                       (empty — clipped to 1e-4)
       66..72│██████████ 10%                       (empty)

  PSI(tenure_months) = 4.8451  ──►  4.8 ≥ 0.2  ──►  DRIFT
```

### 3.3 The form-4 chain across two workflows

```
┌─ 03-drift-detection.yml ── cron 07:00 / PR / manual ──────────────────┐
│  test ──► drift-check (permissions: contents: write)                  │
│             train ► serve ► replay drifted traffic                    │
│             drift pipeline (continue-on-error) ──► outcome: failure   │
│             upload drift-report (if: always)            │             │
│             if outcome == failure:                      ▼             │
│             POST /repos/{repo}/dispatches  {"event_type":             │
│                                             "drift-detected"}        │
└──────────────────────────────────────────────│────────────────────────┘
                                               │  repository_dispatch
                                               ▼  (runs from DEFAULT branch)
┌─ 03-retrain-on-drift.yml ─────────────────────────────────────────────┐
│  on: repository_dispatch: types: [drift-detected]                     │
│  retrain ──► train pipeline (gate) ──► churn-model-retrained artifact │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Walkthrough

All commands run from `lessons/03-drift-detection/`. No new dependencies; PSI is `math.log` and two numpy calls.

### Step 1 — meet the drifted world

```bash
head -n 4 data/traffic_drifted.csv
```

Expected output (exact — `expected_outputs/drifted_traffic_head.txt`):

```
tenure_months,monthly_charges,total_charges,contract_type,payment_method,support_tickets
8,139.87,1118.96,month_to_month,electronic_check,7
19,82.46,1566.74,month_to_month,electronic_check,2
10,120.87,1208.7,month_to_month,electronic_check,2
```

Same schema as `traffic_baseline.csv` (which is byte-identical to Lesson 02's traffic), but: tenure 1–24 instead of 1–72, charges 60–140 instead of 20–120, 75% month-to-month, 60% electronic check, Poisson(3.0) tickets. Every row is a *valid* request. Nothing will error.

### Step 2 — run the tests

```bash
uv run pytest -q
```

Expected output:

```
...............                                                          [100%]
15 passed in 0.29s
```

`test_psi.py` contains the hand-check: PSI of (0.5, 0.5) vs (0.9, 0.1) is `0.8789` — verify it on paper with the formula from §2.2 before trusting the code.

### Step 3 — train and replay the baseline (the healthy day)

```bash
uv run python -m src.pipeline.train_pipeline
```

Terminal 1: `uv run python -m src.serving.run_server` — Terminal 2:

```bash
curl -fsS http://127.0.0.1:8000/health
uv run python -m src.monitoring.traffic_replay
```

Expected output: `{"status":"ok"}` then `sent 200 requests: 192 accepted, 8 rejected` (the replayer defaults to `data/traffic_baseline.csv`).

```bash
uv run python -m src.pipeline.drift_pipeline
```

Expected output (psi values exact; the log path is yours):

```
built reference profiles from data/churn.csv (2000 rows)
read 192 current records from logs/predictions.jsonl
psi by feature: {'tenure_months': 0.0566, 'monthly_charges': 0.0472, 'total_charges': 0.0314, 'support_tickets': 0.0133, 'contract_type': 0.0072, 'payment_method': 0.0025}
report written to reports/drift_report.txt
no drift detected: all features below psi threshold 0.2
```

All six features under 0.1 — *stable*. Note they are not 0.0: two hundred samples of the same distribution still wiggle. That gap between "identical" and "stable" is why thresholds exist.

### Step 4 — the world changes

Fresh window, drifted traffic (server still running):

```bash
rm -rf logs
uv run python -m src.monitoring.traffic_replay data/traffic_drifted.csv
uv run python -m src.pipeline.drift_pipeline
echo "exit code: $?"
```

Why `rm -rf logs` first: the log file is our window. Appending drifted onto baseline would average the two worlds and dilute every PSI — windowing is not a detail, it is half the detector.

Expected output: same replay line (`192 accepted, 8 rejected` — valid requests, remember), then:

```
psi by feature: {'tenure_months': 4.8451, 'monthly_charges': 3.1281, 'total_charges': 2.2862, 'support_tickets': 0.8683, 'contract_type': 0.3224, 'payment_method': 0.3416}
report written to reports/drift_report.txt
```

followed by a traceback ending in:

```
ValueError: data drift detected: {'tenure_months': 4.8451, 'monthly_charges': 3.1281, 'total_charges': 2.2862, 'support_tickets': 0.8683, 'contract_type': 0.3224, 'payment_method': 0.3416} (psi threshold 0.2)
exit code: 1
```

All 6 of 6 features over threshold — and the service never logged a single error. Read `reports/drift_report.txt` (written *before* the gate fired):

```
  feature              psi        status
  tenure_months        4.8451     DRIFT
  monthly_charges      3.1281     DRIFT
  total_charges        2.2862     DRIFT
  support_tickets      0.8683     DRIFT
  contract_type        0.3224     DRIFT
  payment_method       0.3416     DRIFT
```

### Step 5 — byte-exact validation against canonical logs

`expected_outputs/` ships both frozen prediction logs. The pipeline takes a log-path override:

```bash
uv run python -m src.pipeline.drift_pipeline expected_outputs/predictions_log_baseline.jsonl
diff reports/drift_report.txt expected_outputs/drift_report_baseline.txt

uv run python -m src.pipeline.drift_pipeline expected_outputs/predictions_log_drifted.jsonl
diff reports/drift_report.txt expected_outputs/drift_report_drifted.txt
```

Expected: first run exits 0, second exits 1, **both diffs empty**. Full stdout transcripts: `drift_check_baseline_log.txt` and `drift_check_drifted_log.txt`.

### Step 6 — read the chain, then watch it fire

Open both workflow files and map them to §2.4–2.5:

- `03-drift-detection.yml` — cron + PR + manual (with a `traffic_profile` choice input, default **drifted** so the chain demos itself). The `drift-check` job: train → serve+replay → drift pipeline under `continue-on-error` → report artifact `if: always()` → dispatch step guarded by `steps.drift-check.outcome == 'failure'`. Note `permissions: contents: write` on the job.
- `03-retrain-on-drift.yml` — `repository_dispatch: types: [drift-detected]` + manual. Echoes the source run id from `client_payload`, retrains, uploads `churn-model-retrained`.

Push / open the PR, then check the Actions tab against `expected_outputs/workflow_run_summary.txt`. **First-PR caveat** (§2.5 rule 2): the dispatch is sent but the listener isn't on `main` yet — after merge, press "Run workflow" on 03-drift-detection (or wait for the cron) and watch *two* runs appear: the detection run, then, seconds later, the retraining run it summoned. That second run appearing on its own is the whole course so far, working.

---

## 5. Expected outputs — file map

| File | Produced by | Varies between machines |
|---|---|---|
| `drifted_traffic_head.txt` | `head -n 4 data/traffic_drifted.csv` | nothing |
| `pytest_output.txt` | `uv run pytest -q` | duration |
| `train_log.txt` | training | nothing — same as Lessons 01–02 |
| `traffic_replay_baseline_output.txt` / `traffic_replay_drifted_output.txt` | replays (steps 3–4) | nothing |
| `predictions_log_baseline.jsonl` / `predictions_log_drifted.jsonl` | canonical frozen logs (192 each) | n/a — committed references |
| `drift_check_baseline_log.txt` / `drift_check_drifted_log.txt` | pipeline over canonical logs | traceback paths only |
| `drift_report_baseline.txt` / `drift_report_drifted.txt` | same runs | nothing — diffs must be empty |
| `workflow_run_summary.txt` | reading both Actions runs | timings |

Every PSI value is exact: deterministic data + deterministic model + logged features. Latency never enters the drift path — that is why this lesson's outputs are *fully* byte-reproducible, unlike Lesson 02's live-latency fields.

---

## 6. Exercises

Skeletons in `exercises/`, answers in `solutions/`, loop in `exercises/README.md`.

1. **PSI from scratch** (`exercise_1_psi.py`) — the formula, the clipping, the length guard. Valid: `uv run pytest tests/test_psi.py -q` → `4 passed`.
2. **Reference profiles** (`exercise_2_reference_profile.py`) — quantile bin edges, binned proportions, sorted categorical frequencies. Valid: `4 passed`.
3. **Drift gate** (`exercise_3_drift_gate.py`) — at-threshold fires, only drifted features listed. Valid: `3 passed`.
4. **The chain** (`exercise_4_drift_workflow.yml`) — rebuild triggers, `continue-on-error` capture, conditional dispatch, permissions. Validate by diff, then for real on a PR.

Final boss for 1–3: both byte-exact diffs of step 5, with your implementations swapped in.

---

## 7. Validation checklist

- [ ] `uv run pytest -q` prints `15 passed`.
- [ ] I computed PSI of (0.5, 0.5) → (0.9, 0.1) on paper and got 0.8789.
- [ ] Baseline run: all six PSI values < 0.1, exit 0. Drifted run: 6/6 DRIFT, exit 1 — and I can recite both `psi by feature` lines' largest value and why tenure tops the list.
- [ ] I can explain why the drifted run produced **zero** service errors and what that implies about monitoring-without-drift-detection.
- [ ] Both step-5 diffs are empty.
- [ ] I can name the three GitHub rules from §2.5 and point to the YAML line that satisfies each.
- [ ] I can explain `continue-on-error: true` + `steps.<id>.outcome` and the trade-off it accepts.
- [ ] I know why `rm -rf logs` preceded the drifted replay, and what would have happened to the PSI values without it.

---

## 8. Build from scratch

Rebuild order with checkable "done" states. Keep `data/`, `tests/`, and the canonical logs as the harness; platform layers carry over from earlier rebuilds.

1. **`drift/psi.py`** — done: `pytest tests/test_psi.py` → `4 passed` (write the hand-check first, then code until it passes).
2. **`drift/reference_profile.py`** — done: `4 passed`.
3. **`drift/drift_detector.py`** — done: `pytest tests/test_drift_detector.py` → `4 passed`.
4. **`drift/drift_gate.py`** — done: `3 passed`.
5. **`drift/drift_report.py`** — done: rendering the drifted metrics reproduces `drift_report_drifted.txt` byte for byte.
6. **`pipeline/config.py` (DriftConfig) + `pipeline/drift_pipeline.py`** — done: step 5's two runs, exit codes 0 and 1, empty diffs.
7. **`.github/workflows/03-drift-detection.yml` + `03-retrain-on-drift.yml`** — done: a PR run matches `workflow_run_summary.txt`; after merge, a manual run summons the retrain run.

Stuck? The failing test and the expected output are the spec — not `src/`.

---

## Lesson summary

- Data drift is the input distribution leaving the training distribution, and it is detectable the moment it happens — PSI per feature against a frozen reference profile (quantile bins for numeric, frequencies for categorical, ≥ 0.2 means act) — while concept drift must wait for labels.
- The drifted world produced 192 perfect 200-responses and 6/6 features over threshold: services lie, distributions don't, and the inputs you logged in Lesson 02 are what made detection possible.
- Form 4 is a gate failure converted into a signal: `continue-on-error` captures the exit code, an outcome-guarded step POSTs `repository_dispatch` (the `GITHUB_TOKEN` exception that works), and a listener workflow on the default branch retrains — detection summons retraining with no human in the loop.

**Next — Lesson 04 (Containerization + AWS Lambda):** everything so far deploys to `127.0.0.1`. Next the serving system leaves home: Docker image → ECR → Lambda → API Gateway, with the build-once/promote-many pattern from Lesson 00 §2.4 finally made literal — plus OIDC so the pipeline gets AWS credentials without storing a single long-lived secret.
