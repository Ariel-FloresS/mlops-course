# 05 — Deployment Strategies: Blue-Green, Canary, Shadow

Lesson 04 ended with `update-function-code` replacing 100% of production in one atomic shot. For a model — whose correctness is *statistical*, not binary — that is gambling: offline metrics passed the gate, but nobody watched the candidate answer real traffic before it owned all of it.

This lesson builds the three patterns that de-risk the cutover — **blue-green** (instant switch, instant rollback), **canary** (gradual exposure), **shadow** (observe at zero user risk) — as a **runnable local system**: a routing service in front of two live model servers (`blue` = the model you have shipped since Lesson 01; `green` = a candidate retrained on fresh data), plus a **promotion gate** that turns shadow observations into a promote/abstain decision, and a **progressive-deploy pipeline** that chains shadow → gate → canary → switch with the rollback built in as *abstention*.

---

## 1. Objectives

After this lesson you can:

- Explain blue-green, canary, and shadow; pick one per scenario using the cost / detection-speed / user-risk trade-offs.
- State the ML twist: why offline metrics on different test sets are not comparable, and why shadow comparison on identical live traffic is the honest A-vs-B.
- Build a routing layer where the *entire* blue-green switch is one config value, canary is a seeded weighted splitter, and shadow forwards twice but serves once.
- Turn shadow logs into a promotion decision with the same `collect → enforce(if/raise)` gate pattern used for training metrics, monitoring alerts, and drift.
- Read a progressive-deploy pipeline where a red gate **is** the rollback, and map each local pattern to its AWS Lambda primitive (versions, aliases, weighted routing).

---

## 2. Theory

### 2.1 The problem: total replacement is a bet

A deployment strategy answers one question: **who meets the new model, when, and what do we learn before everyone does?** Replace-all answers: "everyone, immediately, nothing". The three classic alternatives:

| | Blue-green | Canary | Shadow |
|---|---|---|---|
| What runs | two full environments; one live | both live; traffic split by weight | both run every request; only blue answers |
| Who meets green | everyone, after an instant switch | a chosen % of users | **nobody** |
| Detects problems | after the switch (fast rollback) | during ramp-up, on a blast radius you chose | before any exposure |
| Rollback | flip the pointer back (seconds) | set weight to 0 | nothing to roll back |
| Cost | 2× infrastructure during transition | 2× during ramp | 2× compute on **every** shadowed request |
| Blind spot | everyone exposed at once, briefly | small samples are noisy; needs metrics to judge | response is discarded — no user-behavior signal |

They compose in sequence — and that composition is this lesson's pipeline: **shadow** (prove it harmless) → **canary** (prove it under partial fire) → **blue-green switch** (make it official, keep blue warm for rollback).

### 2.2 The ML twist: deployment strategies are model comparison

For ordinary software, a canary mostly watches error rates and latency. A model can be *wrong with 200s* (Lesson 03's whole point), so judging green needs **model-level comparison** — and here offline evaluation betrays you:

blue scored `roc_auc 0.9222` on *its* test split; green scores `0.9099` on *its own, different* split (more data, different 20%). Those two numbers are **not comparable** — different exams. The honest comparison is both models answering the **same live requests**: that is shadow mode, and it is why shadow is the king pattern for ML. Our shadow log stores both answers per request; the comparator reduces 192 paired predictions to `label_agreement_rate`, `disagreement_count`, `mean/max_probability_delta` — green vs blue on identical inputs, no exam bias.

(What shadow still cannot see: outcome quality. Agreement says "green behaves like blue", not "green is better". Judging *better* needs labels — the registry + evaluation story of Lesson 06.)

### 2.3 The router: all three patterns are one `if`

The architecture is a **routing service** (port 8000) in front of two **model servers** (blue 8001, green 8002 — each is Lesson 01's app serving its own artifact). Everything interesting lives in one endpoint:

- `mode == "blue"` or `"green"` → the mode name *is* the target name. The blue-green switch — the whole pattern — is a one-word config change; rollback is changing it back. Atomicity comes free because the router is the single entry point.
- `mode == "canary"` → a `WeightedTrafficSplitter` (seeded RNG) picks blue or green per request. Seeded means the assignment *sequence* is reproducible — your walkthrough and CI assert the exact same 2-of-10 green assignments. Real routers use randomness too (or sticky hashing); the seed is our determinism discipline, same as every lesson.
- `mode == "shadow"` → forward to blue, forward to green, log both predictions, **return blue's**. The response contract never changes; observability rides in the `X-Served-By` response header instead of the body — clients keep their contract, operators get their signal.

Two design notes worth stealing. The **forwarder is injected** (`forwarder: Callable`), so the router's tests inject a fake returning canned predictions — routing logic gets tested with zero servers running. And our shadow mirror is **synchronous and fail-loud**: if green dies mid-shadow, the request dies too. Production shadow isolates the mirror path (async, errors suppressed) precisely because shadow must never hurt users; we keep the course's fail-loud standard, and name the hardening you would add.

One architecture refinement this lesson makes explicit: `run_router` / `run_model_server` import `pipeline/config.py`. Entry-point `run_*` scripts are **composition roots** — peers of the pipeline layer, allowed to touch config. The request-path code (`router.py`, `model_server.py`) remains config-free and fully injected.

### 2.4 Promotion gates, and rollback as abstention

The shadow log feeds the fourth gate of this course (training metrics → monitoring alerts → drift PSI → **promotion**): `collect_promotion_blockers` (pure, testable) + `enforce_promotion_gate` (`if/raise`). Thresholds: agreement ≥ 0.9, mean probability delta ≤ 0.1, ≥ 150 comparisons (decide on evidence, not anecdotes).

In the pipeline, the gate sits **between shadow and canary**. If it raises: exit 1, red job, stages 3–4 never run, blue keeps 100% of traffic. Read that again — **nothing performed a rollback; the promotion simply did not happen.** Progressive deployment's deepest idea is that the safe state is the default state, and every advance must pass a gate. (The report still uploads via `if: always()` — the artifact that explains a red gate is the valuable one.)

### 2.5 The same patterns on AWS Lambda (documented, not executed)

Lesson 04's primitives map one-to-one; values are shapes, ids are yours:

```bash
aws lambda publish-version --function-name churn-predictor
```
→ `{"Version": "2", ...}` — an immutable snapshot of code + config (our "green" image digest, frozen).

```bash
aws lambda create-alias --function-name churn-predictor --name live --function-version 1
```
→ the **alias** is the router: API Gateway points at `live`, never at a version.

```bash
aws lambda update-alias --function-name churn-predictor --name live \
  --routing-config '{"AdditionalVersionWeights": {"2": 0.2}}'
```
→ **canary, natively**: 80% version 1, 20% version 2 — our `canary_green_weight` as a managed feature.

```bash
aws lambda update-alias --function-name churn-predictor --name live --function-version 2
```
→ the blue-green switch (and the rollback is the same command with `--function-version 1`).

Shadow has no Lambda one-liner — you build it (a dispatcher invoking both versions, or CloudWatch-based offline replay), which is exactly why we built it by hand. Managed wrappers exist (CodeDeploy drives weighted aliases with automatic CloudWatch-alarm rollback) — same pattern, different driver. GitHub `environments` with required reviewers add a human approval between canary and switch; we note it and keep the course self-approving.

---

## 3. Diagrams

### 3.1 Three patterns, one picture

```
BLUE-GREEN                      CANARY                          SHADOW

users ──► router                users ──► router                users ──► router
            │ mode=blue                     │ weighted                      │ every request
            ▼                               │ splitter                      ▼
        ┌──────┐                    80%     │     20%                   ┌──────┐ answers
        │ BLUE │ ◄── 100%          ┌────────┴───────┐                   │ BLUE │────► user
        └──────┘                   ▼                ▼                   └──────┘
        ┌──────┐  idle,        ┌──────┐         ┌──────┐                ┌──────┐ same request,
        │GREEN │  warm,        │ BLUE │         │GREEN │                │GREEN │ answer logged,
        └──────┘  ready        └──────┘         └──────┘                └──────┘ NEVER served
            ▲
   switch = mode=green         judge green on its slice         judge green on everything,
   rollback = mode=blue        before widening it               at zero user risk
```

### 3.2 The local fleet

```
                          ┌─ router :8000  (mode: blue|green|canary|shadow) ─┐
 traffic ───► /predict ──►│  X-Served-By header = who answered              │
                          │  shadow mode: forward twice, serve blue,        │
                          │  log the pair ────────────────────────────────┐ │
                          └───────┬──────────────────────────┬────────────│─┘
                                  ▼                          ▼            ▼
                     model server :8001          model server :8002   logs/shadow_predictions.jsonl
                     artifacts/blue/             artifacts/green/         │
                     (churn.csv, 2000 rows,      (churn_v2.csv, 3000     ▼
                      roc_auc 0.9222)             rows, roc_auc 0.9099)  promotion pipeline
                                                                          compare → report → gate
                                                                          pass: green may take traffic
                                                                          fail: ValueError, exit 1
```

### 3.3 The progressive pipeline (stages and the gate that guards them)

```
test ──► train blue + green ──► start fleet
                                    │
                                    ▼
                     stage 1: SHADOW   replay 200 requests through mode=shadow
                                    │  users met only blue; 192 paired predictions logged
                                    ▼
                     stage 2: GATE     promotion pipeline: compare → report → enforce
                                    │ pass                        │ fail
                                    ▼                             ▼
                     stage 3: CANARY   mode=canary,          job RED here.
                                    │  assert exact          stages 3-4 never run.
                                    │  2/10 green            blue keeps 100%.
                                    ▼                        report uploaded anyway.
                     stage 4: SWITCH   mode=green, assert X-Served-By: green
                                       + green's exact probability
```

---

## 4. Walkthrough

All commands run from `lessons/05-deployment-strategies/`. The fleet needs several terminals (or `&`-background them as shown). No new dependencies.

### Step 1 — run the tests

```bash
uv run pytest -q
```

Expected output:

```
................                                                         [100%]
16 passed in 4.03s
```

Read `tests/test_router.py` first: a `fake_forwarder` returns canned predictions per endpoint, so all four routing behaviors are verified with no servers, no models, no network — the injected-collaborator payoff, again.

### Step 2 — train blue and green

```bash
uv run python -m src.pipeline.train_pipeline blue
uv run python -m src.pipeline.train_pipeline green
```

Expected outputs (exact — `train_blue_log.txt`, `train_green_log.txt`): blue is the canonical model (`roc_auc 0.9222`, from `data/churn.csv`, artifacts in `artifacts/blue/`); green trains on `data/churn_v2.csv` — the original 2,000 rows plus 1,000 fresh ones (seed 99, same generator: the "new labeled data arrived after Lesson 03's drift episode" story) — and scores:

```
test metrics: {'accuracy': 0.85, 'precision': 0.7738, 'recall': 0.7143, 'roc_auc': 0.9099}
```

Pause on this: green's 0.9099 vs blue's 0.9222 does **not** mean green is worse — different test splits, different exams (§2.2). Both clear the 0.85 training gate; which one *behaves* better on production traffic is exactly what shadow will measure.

### Step 3 — start the fleet, meet the steady state

Terminals 1–3 (or background each with `&`):

```bash
uv run python -m src.serving.run_model_server blue
uv run python -m src.serving.run_model_server green
uv run python -m src.serving.run_router blue
```

Terminal 4 — the high-risk request through the router in `blue` mode:

```bash
curl -fsS -D - -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"tenure_months": 2, "monthly_charges": 95.0, "total_charges": 190.0, "contract_type": "month_to_month", "payment_method": "electronic_check", "support_tickets": 4}' \
  | grep -iE "x-served-by|churn"
```

Expected output (exact — `blue_mode_response.txt`):

```
x-served-by: blue
{"churn_probability":0.9966,"churn_label":1}
```

The familiar 0.9966, now answered through a router that could be doing four different things — and the header tells you which.

### Step 4 — stage 1: shadow green behind blue

Restart the router in shadow mode (Ctrl-C terminal 3, then):

```bash
uv run python -m src.serving.run_router shadow
```

Replay production traffic (terminal 4):

```bash
uv run python -m src.monitoring.traffic_replay
wc -l logs/shadow_predictions.jsonl
head -n 1 logs/shadow_predictions.jsonl
```

Expected output: `sent 200 requests: 192 accepted, 8 rejected`, then `192` shadow records. Every record carries the features plus **both** verdicts:

```
{"blue_label": 0, "blue_probability": 0.0076, ..., "green_label": 0, "green_probability": 0.0089, ...}
```

Every client got blue's answer; green just took the same 192-question exam, silently.

### Step 5 — stage 2: the promotion gate

```bash
uv run python -m src.pipeline.promotion_pipeline
```

Expected output shape (your timestamps differ; metric values exact — and byte-exact against the canonical log below):

```
read 192 shadow comparison records from logs/shadow_predictions.jsonl
comparison metrics: {'comparison_count': 192, 'label_agreement_rate': 0.9896, 'disagreement_count': 2, 'mean_probability_delta': 0.0102, 'max_probability_delta': 0.0502}
report written to reports/promotion_report.txt
promotion gate passed: green is safe to receive traffic
```

Two disagreements in 192 — and they live near the 0.5 boundary, not on obvious profiles (check the report in `reports/`). Byte-exact validation, canonical-log style:

```bash
uv run python -m src.pipeline.promotion_pipeline expected_outputs/shadow_log_sample.jsonl
diff reports/promotion_report.txt expected_outputs/promotion_report.txt
```

Expected: exit 0, empty diff (`promotion_pipeline_log.txt` has the full stdout). And the blocked case, thresholds tightened to absurdity over the same data:

```bash
uv run python -c "
from dataclasses import replace
from pathlib import Path
from src.deployment.promotion_gate import PromotionThresholds
from src.pipeline.config import DEFAULT_PROMOTION_CONFIG
from src.pipeline.promotion_pipeline import run_promotion_pipeline
strict_thresholds = PromotionThresholds(
    min_label_agreement_rate=0.999,
    max_mean_probability_delta=0.1,
    min_comparison_count=150,
)
run_promotion_pipeline(
    replace(
        DEFAULT_PROMOTION_CONFIG,
        shadow_log_path=Path('expected_outputs/shadow_log_sample.jsonl'),
        thresholds=strict_thresholds,
    )
)
"
echo "exit code: $?"
```

Expected tail (`promotion_blocked_log.txt`):

```
ValueError: promotion blocked: ['label_agreement_rate=0.9896 is below minimum 0.999']
exit code: 1
```

### Step 6 — stage 3: canary at 20%

Restart the router in canary mode, then send the same request ten times watching the header:

```bash
uv run python -m src.serving.run_router canary
```

```bash
for i in $(seq 1 10); do
  curl -fsS -D - -o /dev/null -X POST http://127.0.0.1:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"tenure_months": 2, "monthly_charges": 95.0, "total_charges": 190.0, "contract_type": "month_to_month", "payment_method": "electronic_check", "support_tickets": 4}' \
    | grep -i x-served-by
done
```

Expected output — **exact**, because the splitter is seeded (13) and the router just started (`canary_header_sequence.txt`):

```
x-served-by: blue
x-served-by: blue
x-served-by: blue
x-served-by: blue
x-served-by: green
x-served-by: blue
x-served-by: blue
x-served-by: green
x-served-by: blue
x-served-by: blue
```

Requests 5 and 8 went to green: 2 of 10 at weight 0.2. Identical inputs, different servers, chosen by the router — that is a canary. (In CI this very sequence is asserted with `test "$green_count" -eq 2`.)

### Step 7 — stage 4: the blue-green switch

Restart the router one last time:

```bash
uv run python -m src.serving.run_router green
```

Repeat the step-3 curl. Expected output (exact — `green_switch_response.txt`):

```
x-served-by: green
{"churn_probability":0.9968,"churn_label":1}
```

Green now answers 100% — with *its* probability, 0.9968, not blue's 0.9966. The switch was one word of config; the rollback would be the same word, backwards. Blue is still running on 8001, warm, untouched: that standby instance **is** the blue-green pattern.

### Step 8 — read the pipeline, then watch it

`.github/workflows/05-progressive-deploy.yml` is this walkthrough as a six-step job — train both → fleet up → shadow replay → **gate** → canary (with the exact 2-of-10 assertion) → switch (asserting green's exact 0.9968). Push/open the PR and compare with `expected_outputs/workflow_run_summary.txt`, especially the failure mode: a red gate means stages 3–4 simply never exist.

---

## 5. Expected outputs — file map

| File | Produced by | Varies |
|---|---|---|
| `pytest_output.txt` | `uv run pytest -q` | duration |
| `train_blue_log.txt` / `train_green_log.txt` | step 2 | nothing |
| `blue_mode_response.txt` | step 3 curl | nothing |
| `traffic_replay_output.txt` | step 4 replay | nothing |
| `shadow_log_sample.jsonl` | canonical frozen shadow log (192 paired records) | n/a — committed reference |
| `promotion_pipeline_log.txt` / `promotion_report.txt` | pipeline over the canonical log | nothing — diff must be empty |
| `promotion_blocked_log.txt` | step 5 strict-thresholds demo | traceback paths |
| `canary_header_sequence.txt` | step 6 (fresh router, seed 13) | nothing |
| `green_switch_response.txt` | step 7 curl | nothing |
| `workflow_run_summary.txt` | reading the Actions run | timings |

Note what is exact here that has no right to be in ordinary systems: the canary *assignment sequence*. Seeded randomness keeps even traffic-splitting reproducible — the discipline that lets a course (and a CI job) assert on a coin flip.

---

## 6. Exercises

Skeletons in `exercises/`, answers in `solutions/`, loop in `exercises/README.md`.

1. **The router** (`exercise_1_router.py`) — implement `build_shadow_record` and the four-mode `predict` endpoint (shadow forwards twice serves once; canary asks the splitter; blue/green: the mode *is* the target). Valid: `uv run pytest tests/test_router.py -q` → `4 passed`.
2. **Shadow comparator** (`exercise_2_shadow_comparator.py`) — paired predictions → agreement + delta metrics. Valid: `3 passed`.
3. **Promotion gate** (`exercise_3_promotion_gate.py`) — blockers + enforce. Valid: `4 passed`.
4. **The progressive pipeline** (`exercise_4_workflow.yml`) — rebuild the four stages, the gate placement, and the two exact assertions from memory.

Final boss for 1–3: the byte-exact diff of step 5 with your implementations swapped in.

---

## 7. Validation checklist

- [ ] `uv run pytest -q` prints `16 passed`, and I can explain how the router tests run with zero servers.
- [ ] I can fill the 6-row comparison table (§2.1) from memory and pick a pattern for: a payment-fraud model, a UI recommender tweak, a latency-critical rewrite.
- [ ] I can explain why blue's 0.9222 vs green's 0.9099 proves nothing, and what the shadow comparison measures instead.
- [ ] My shadow run logs exactly 192 paired records and the promotion report diffs empty against the canonical one.
- [ ] Strict-threshold demo prints `exit code: 1` *after* the report is written.
- [ ] My canary sequence is exactly requests 5 and 8 to green, and I know why it is reproducible.
- [ ] Step 7 returns `x-served-by: green` with `0.9968` — and I can state what the rollback command would be.
- [ ] I can answer: when the gate fails in CI, what performs the rollback? (Nothing. That is the design.)
- [ ] I can map mode=green / canary_green_weight / the router itself to their three Lambda primitives.

---

## 8. Build from scratch

Keep `data/`, `tests/`, and the canonical shadow log as the harness; platform layers carry over from earlier rebuilds.

1. **`deployment/traffic_splitter.py`** — done: `pytest tests/test_traffic_splitter.py` → `5 passed`.
2. **`deployment/shadow_comparator.py`** — done: `3 passed` (hand-compute the 4-record example first).
3. **`deployment/promotion_gate.py` + `promotion_report.py`** — done: `4 passed`; rendering the canonical metrics reproduces `promotion_report.txt`.
4. **`serving/model_server.py` + `run_model_server.py`** — done: both servers answer `/health`; blue returns 0.9966 on the high-risk profile at :8001.
5. **`serving/router.py` + `run_router.py`** — done: `pytest tests/test_router.py` → `4 passed`; then live: step 3's exact output.
6. **`pipeline/config.py` (two TrainingConfigs, endpoints, routing + promotion configs) + `pipeline/promotion_pipeline.py`** — done: step 5's byte-exact diff and exit codes.
7. **`.github/workflows/05-progressive-deploy.yml`** — done: a PR run matches `workflow_run_summary.txt`, including `green assignments in first 10 requests: 2`.

Stuck? The failing test and the expected output are the spec — not `src/`.

---

## Lesson summary

- Blue-green, canary, and shadow answer "who meets the new model, when": instant-switch with a warm standby, gradual weighted exposure, and zero-risk observation — and they compose into one progressive pipeline: shadow → gate → canary → switch.
- For models the judgement must be comparative on identical traffic — offline metrics from different test splits are different exams — so the shadow log of paired predictions feeds a promotion gate (agreement 0.9896, 2 disagreements of 192) built from the same collect + if/raise pattern as every gate in this course.
- The router makes the patterns almost free: the mode name is the target (blue-green in one word), a seeded splitter is the canary (assignment sequence reproducible enough for CI to assert 2-of-10), and a red promotion gate rolls back by pure abstention — stages that never run.

**Next — Lesson 06 (MLflow):** this lesson juggled `artifacts/blue/` and `artifacts/green/` by directory name — version management by folder convention, which collapses the moment there are three candidates or one question: "what exactly is in production, and how was it trained?" A **model registry** answers with versions, stages, lineage, and reproducibility metadata; MLflow gives the course its registry, and the gates you have built start promoting *registry stages* instead of file paths.
