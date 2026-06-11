# 00 — Setup & The ML CI/CD Pipeline Landscape

This lesson has two jobs: get your environment ready, and install the **mental model** the whole course is built on — what an ML CI/CD pipeline is, the different forms it can take, and how GitHub Actions (our pipeline engine for the entire course) is anatomically structured.

Lesson 01 starts building immediately. Everything here is the map you will use to not get lost there.

---

## 1. Objectives

After this lesson you can:

- Set up the course environment with `uv` and validate it against expected outputs.
- Explain why CI/CD for ML is different from classic software CI/CD.
- Name the six forms of ML pipelines (from manual notebooks to event-driven retraining) and pick the right one for a scenario.
- Read a GitHub Actions workflow file and identify its triggers, jobs, steps, and artifacts.
- Recognize the generic training-pipeline DAG that every lesson in this course is a variation of.
- Read course code fluently: layered architecture, dependency injection, fail-loud validation.

---

## 2. Theory

### 2.1 Why ML needs its own CI/CD

Classic software delivery automates one moving part: **code**.

```
code change ──► build ──► test ──► deploy
```

A build either compiles or it doesn't. A test either passes or it doesn't. Given the same code, the pipeline produces the same binary, forever. The pipeline ends at deploy.

ML systems have **three** moving parts: **code**, **data**, and the **model artifact** that the first two produce together. That breaks four assumptions of classic CI/CD:

| Dimension | Classic software CI/CD | ML CI/CD |
|---|---|---|
| What changes | code | code, data, or both |
| What "passing" means | binary (tests green) | metric clears a threshold (a *quality gate*: e.g. `roc_auc >= 0.85`) |
| The artifact | a build, reproducible from code alone | a model, reproducible only from code **+ data + seed** |
| When it's done | at deploy | never — deployed models decay as the world drifts, so the pipeline loops back |

The consequence: an ML pipeline is not "CI/CD with a training step bolted on". It needs **data validation** before training, **metric gates** after training, **versioned artifacts** that travel separately from code, and eventually a **feedback loop** (monitoring → drift signal → retrain) that classic pipelines simply don't have.

The industry shorthand for this extended loop is **CI/CD/CT**:

- **CI** — continuous integration: test the *code* (including the pipeline code itself).
- **CD** — continuous delivery: ship the *serving system* that exposes the model.
- **CT** — continuous training: re-produce the *model* when code, data, or the world changes.

### 2.2 The six forms of ML pipelines

Every real-world ML pipeline you will meet is one of these forms (or a combination). They are ordered by increasing automation of the **trigger** — *what runs the pipeline* matters more than *what the pipeline runs*.

| Form | Name | Trigger | What is automated | What breaks first | Lesson |
|---|---|---|---|---|---|
| 0 | Notebook-driven | a human, cell by cell | nothing | reproducibility ("works on my machine") | — |
| 1 | Scripted | a human runs `train.py` | the steps, not the trigger | history: nobody knows which run produced the deployed model | — |
| 2 | CI-triggered training | `git push` / pull request | full train → gate → package, on every code change | data is still static; model never refreshes on its own | **01** |
| 3 | Scheduled retraining | cron (`schedule:` in Actions) | retraining cadence | retrains blindly — burns compute even when nothing changed, and misses sudden drift between runs | 02–03 |
| 4 | Event-driven retraining | a monitoring signal (drift, metric decay) | retrain exactly when needed | requires monitoring + drift detection to exist first | **03** |
| 5 | Orchestrated DAGs | a workflow engine (Airflow, Prefect, Kubeflow) | complex multi-model graphs, backfills, retries | infrastructure overhead; overkill for a single model | mentioned only |

Three things to internalize:

1. **Forms compose.** A mature system is usually 2 + 3 + 4 at once: push-triggered for code changes, scheduled as a safety net, event-driven for drift. This course builds exactly that stack, in that order.
2. **The gate is what makes it safe.** Forms 2–5 are only trustworthy because a metric gate can abort a bad model before it ships. Automation without gates is just faster failure.
3. **This course stops at form 4.** GitHub Actions covers forms 2–4 perfectly for a single model, which is why the course never needs an external orchestrator. Form 5 exists for when you have dozens of interdependent pipelines — recognize it, don't reach for it first.

### 2.3 MLOps maturity levels

The pipeline forms map onto the standard maturity model (popularized by Google's MLOps whitepaper):

- **Level 0 — manual process.** Forms 0–1. The "pipeline" is a person. Deployment is a handoff of a model file.
- **Level 1 — automated training pipeline.** Forms 2–4. Training, gating, and packaging are code, triggered automatically. This is where continuous training (CT) lives. **Lessons 01–03 take you from level 0 to level 1.**
- **Level 2 — automated CI/CD of the pipeline itself.** The pipeline code is tested, versioned, and deployed like any product. Lessons 04–06 (containers, deployment strategies, registry) build the level-2 muscles.

### 2.4 Two pipelines, not one

A common beginner mistake is one giant pipeline that trains *and* serves. Production systems separate them, connected only by a versioned artifact:

- **Training pipeline** (CT): data → validate → features → train → evaluate → gate → **publish artifact** (`model` + `metrics`).
- **Serving pipeline** (CD): take a *published* artifact → package it into a server/container → deploy → smoke test.

The separation buys you: independent failure (a broken deploy doesn't lose a good model), **build once / promote many** (the same artifact goes to staging and production — never rebuilt in between), and instant rollback (point serving back at the previous artifact). Lesson 01 builds both halves and the artifact handoff between them.

### 2.5 Anatomy of a GitHub Actions workflow

GitHub Actions is the pipeline engine for the whole course. The vocabulary, once:

- **Workflow** — one YAML file in `.github/workflows/`. One workflow = one pipeline.
- **Trigger (`on:`)** — what starts it: `push`, `pull_request`, `schedule` (cron), `workflow_dispatch` (manual button), `repository_dispatch` (external event — how lesson 03 wires drift → retrain).
- **Job** — a group of steps running on a fresh virtual machine (a **runner**, e.g. `ubuntu-latest`). Jobs run in parallel unless chained with `needs:`.
- **Step** — a shell command (`run:`) or a reusable **action** (`uses:`, e.g. `actions/checkout@v4`).
- **Artifact** — files uploaded from one job (`actions/upload-artifact`) and downloadable by later jobs or humans. This is how the trained model travels out of the training job.
- **Secrets / variables** — credentials and config injected at runtime, never committed.

A minimal training workflow, the shape you will see (and write) in lesson 01:

```yaml
name: churn-training
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - run: uv run pytest
  train:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - run: uv run python -m src.pipeline.train_pipeline
      - uses: actions/upload-artifact@v4
        with:
          name: churn-model
          path: artifacts/
```

How to read it: one workflow named `churn-training`, triggered by pushes to `main`, two jobs. The `train` job declares `needs: test`, so it only starts if `test` finished green — that dependency is the entire "CI before CT" guarantee. Each job starts from a blank runner, which is why both jobs repeat checkout + uv setup. The final step uploads everything under `artifacts/` so the model survives after the runner is destroyed.

---

## 3. Diagrams

### 3.1 Classic CI/CD vs ML CI/CD/CT

```
CLASSIC SOFTWARE                          ML SYSTEM

┌─────────────┐                           ┌─────────────┬─────────────┬──────────────┐
│ code change │                           │ code change │ data change │ drift signal │
└──────┬──────┘                           └──────┬──────┴──────┬──────┴──────┬───────┘
       ▼                                         └─────────────┼─────────────┘
┌─────────────┐                                                ▼
│    build    │                                         ┌─────────────┐
└──────┬──────┘                                         │    train    │
       ▼                                                └──────┬──────┘
┌─────────────┐                                                ▼
│    test     │  pass/fail is binary                    ┌─────────────┐
└──────┬──────┘                                         │  evaluate   │
       ▼                                                └──────┬──────┘
┌─────────────┐                                                ▼
│   deploy    │ ──► done                                ┌─────────────┐   fail: abort,
└─────────────┘                                         │ metric gate │──► keep current
                                                        └──────┬──────┘    model
                                                               │ pass
                                                               ▼
                                                        ┌─────────────┐
                                                        │   deploy    │
                                                        └──────┬──────┘
                                                               ▼
                                                        ┌─────────────┐
                                                        │   monitor   │──► drift signal
                                                        └─────────────┘    (loops back to top)
```

### 3.2 The generic training-pipeline DAG

Every training pipeline in this course is a variation of this exact sequence:

```
raw data ──► validate ──► build ──► train ──► evaluate ──► metric ──pass──► package ──► publish
             schema       features                          gate            model +      artifact
             & rules                                          │             metadata
                                                              │ fail
                                                              ▼
                                                     abort the run,
                                                     keep last good model
```

The gate placement is the design decision: **after** evaluation, **before** anything is packaged or published. Nothing that failed the gate ever becomes an artifact.

### 3.3 GitHub Actions anatomy

```
.github/workflows/churn-training.yml
┌───────────────────────────────────────────────────────────────────┐
│  workflow: churn-training        on: push to main  (trigger)      │
│                                                                   │
│  ┌──────────────────────┐  needs   ┌──────────────────────────┐   │
│  │ job: test            │ ◄─────── │ job: train               │   │
│  │ runner: ubuntu       │          │ runner: ubuntu           │   │
│  │  1. checkout         │          │  1. checkout             │   │
│  │  2. setup uv         │          │  2. setup uv             │   │
│  │  3. uv run pytest    │          │  3. uv run train         │   │
│  └──────────────────────┘          │  4. upload artifact ─────┼───┼──► artifact store
│                                    └──────────────────────────┘   │    (model + metrics,
└───────────────────────────────────────────────────────────────────┘     survives the runner)
```

---

## 4. Walkthrough: environment setup

The course uses **one** root environment, managed by `uv`, for all lessons. Dependencies are added incrementally as lessons need them — right now the project has zero dependencies on purpose.

Versions in the outputs below are illustrative; yours will be equal or newer. Structure of the output is what you validate, not exact version numbers.

### Step 1 — install uv

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Validate:

```bash
uv --version
```

Expected output (shape):

```
uv 0.7.13
```

### Step 2 — install the pinned Python

The repo pins its interpreter in `.python-version`. From the repo root:

```bash
uv python install
```

Expected output (first time):

```
Installed Python 3.12.11 in 2.34s
 + cpython-3.12.11-linux-x86_64-gnu
```

If already installed, the command exits silently — that is also a pass.

### Step 3 — create the environment

```bash
uv sync
```

Expected output (shape; package counts grow as lessons add dependencies):

```
Using CPython 3.12.3 interpreter at: /usr/bin/python3.12
Creating virtual environment at: .venv
Resolved 33 packages in 4ms
Installed 30 packages in 36ms
```

The exact versions installed come from the committed `uv.lock` — that file is what makes every learner's environment identical, which in turn is what makes the expected outputs of later lessons exact instead of approximate.

### Step 4 — sanity check

```bash
uv run python -c "import sys; print(sys.version_info[:2])"
```

Expected output:

```
(3, 12)
```

### Step 5 — tour the repo

```bash
ls
```

Expected output:

```
00-setup  lessons  pyproject.toml  README.md  shared
```

(`.github/`, `.python-version`, `.gitignore`, and `.venv/` are there too — `ls -a` shows them.)

---

## 5. Expected outputs — consolidated

| Command | Expected output | Pass criterion |
|---|---|---|
| `uv --version` | `uv 0.x.y` | any version prints |
| `uv python install` | `Installed Python 3.12.x ...` or silence | exit code 0 |
| `uv sync` | `Creating virtual environment at: .venv` + `Resolved N packages` | `.venv/` exists afterwards |
| `uv run python -c "import sys; print(sys.version_info[:2])"` | `(3, 12)` | exact match |

---

## 6. Exercises

Lesson 00 is conceptual, so the exercises are paper-based. Answer first, then open the solution.

### Exercise 1 — classify the pipeline form

For each scenario, assign a form (0–5) from section 2.2:

- **a)** A fraud team's model retrains every night at 02:00 via a cron trigger, regardless of what happened that day.
- **b)** A data scientist keeps the production model in a notebook; when asked for a refresh, she re-runs all cells and emails the `.pkl` file.
- **c)** Every merge to `main` runs tests, retrains the churn model, and blocks publishing if ROC-AUC drops below 0.85.
- **d)** A monitoring job computes feature drift daily; when drift exceeds a threshold it fires a `repository_dispatch` event that launches retraining.

<details>
<summary>Solution</summary>

- **a)** Form 3 — scheduled retraining. Automated cadence, blind to need.
- **b)** Form 0 — notebook-driven. The human is the pipeline.
- **c)** Form 2 — CI-triggered training with a metric gate. This is lesson 01.
- **d)** Form 4 — event-driven retraining. This is lesson 03.

</details>

### Exercise 2 — read a workflow

Using the YAML in section 2.5, answer:

1. What event starts the pipeline, and on which branch?
2. Can `train` ever run if `pytest` fails?
3. Why does each job repeat `checkout` and `setup-uv`?
4. After the workflow finishes, where does the trained model live — the runner, the repo, or somewhere else?

<details>
<summary>Solution</summary>

1. A `push` to `main`.
2. No. `needs: test` makes `train` start only after `test` succeeds.
3. Each job runs on a **fresh** runner VM; nothing from another job's filesystem survives, so every job rebuilds its own workspace.
4. Somewhere else: the artifact store, via `upload-artifact`. The runner is destroyed; the repo never receives the model file.

</details>

### Exercise 3 — place the gate

Order these stages into the generic training DAG and mark where a failed gate aborts: `train`, `publish artifact`, `validate data`, `evaluate`, `metric gate`, `build features`, `package`.
Then answer: why must the gate sit before `package`, not after?

<details>
<summary>Solution</summary>

```
validate data → build features → train → evaluate → metric gate → package → publish artifact
                                                         │ fail
                                                         ▼
                                                       abort
```

The gate sits before `package` so that **no failing model ever becomes an artifact**. If packaging happened first, a bad model would already exist as a publishable object — one mistaken click (or one buggy script) away from production.

</details>

---

## 7. Validation checklist

- [ ] `uv --version` prints a version.
- [ ] `.venv/` exists and `uv run python -c "import sys; print(sys.version_info[:2])"` prints `(3, 12)`.
- [ ] I can state the three moving parts of an ML system and the four broken assumptions from section 2.1.
- [ ] Given a scenario, I can assign a pipeline form 0–5 and justify it.
- [ ] In a workflow YAML I can point at: the trigger, the jobs, the dependency between jobs, and where artifacts leave the runner.
- [ ] I can draw the generic training DAG from memory, with the gate in the right place.

---

## 8. Build from scratch

The lesson-00 version of "rebuild it yourself":

1. On paper, redraw diagram 3.2 (the training DAG) from memory. Check against the original.
2. Write the forms table (section 2.2) from memory: form, trigger, what breaks first. Check yourself.
3. On a clean machine (or after deleting `.venv/`), redo the walkthrough in section 4 without looking at it, validating each step against section 5.
4. Write, by hand, the smallest GitHub Actions YAML that runs `uv run pytest` on every push. Compare with the `test` job in section 2.5.

---

## 9. Course code standards — the contract

Every line of reference code, exercise, and solution in this course obeys five rules. Read this once, carefully; lessons will not re-explain it.

**1. No comments, no docstrings.** Names carry all the meaning.
**2. Single responsibility, layered.** Each module belongs to one layer: `data / features / model / serving / pipeline`. A function does one thing.
**3. Dependency injection.** Functions receive their collaborators as parameters. Nothing builds its own dependencies internally — that is what the `pipeline` layer is for.
**4. Fail loud.** Preconditions are checked with `if` + `raise ValueError`. Never defensive `try/except`.
**5. Explicit names.** Long and unambiguous beats short and clever.

What that looks like. **Not** course style:

```python
def process(df):
    try:
        df = df.dropna()
        model = LogisticRegression()
        model.fit(df.drop("churn", axis=1), df["churn"])
        joblib.dump(model, "model.joblib")
    except Exception:
        pass
```

One function loads, cleans, trains, and saves (four responsibilities); it builds its own model (no injection); it swallows every error (defensive `try/except`); `process` and `df` say nothing.

Course style for the same intent:

```python
def validate_required_columns(frame: pd.DataFrame, required_columns: list[str]) -> None:
    missing_columns = [column for column in required_columns if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"missing required columns: {missing_columns}")


def train_classifier(model: ClassifierMixin, features: pd.DataFrame, target: pd.Series) -> ClassifierMixin:
    if len(features) != len(target):
        raise ValueError("features and target must have the same length")
    model.fit(features, target)
    return model
```

Each function has one job and a name that states it; the model arrives injected (`model: ClassifierMixin`), so tests can pass a dummy and lesson 06 can swap implementations without touching this code; bad input raises immediately with a message that names the problem. The `pipeline` layer — and only that layer — wires concrete pieces together.

---

## Lesson summary

- ML CI/CD differs from software CI/CD because data and model artifacts move independently of code, "passing" is a metric gate, and the pipeline loops back through monitoring.
- All ML pipelines are one of six forms, ordered by trigger automation; this course builds forms 2 → 3 → 4 on GitHub Actions, which is MLOps maturity level 0 → 1 in practice.
- Your environment is one uv-managed root project; every lesson validates by comparing against committed expected outputs.

**Next — Lesson 01:** build the real thing: a layered churn training pipeline (data → features → model), local FastAPI serving, and a GitHub Actions workflow with tests, a metric gate, and a published model artifact.
