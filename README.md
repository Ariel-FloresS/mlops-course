# MLOps Course — From a Churn Model to a Mini-LLM, the CI/CD Way

A hands-on, incremental MLOps course built as a repository you **read, trace by hand, and rebuild from scratch**.

The focus is **MLOps engineering**: CI/CD pipelines with GitHub Actions, deployment, monitoring, drift detection, model registries. The models themselves stay deliberately simple (binary churn classification on local synthetic data) so the operational machinery is always the protagonist — not the model science.

## How this course works

You do **not** need to execute the reference code to learn from it. Every lesson is designed around a manual-validation loop:

1. **Read** — the lesson `README.md` explains the *why* before the *how*, with architecture and data-flow diagrams.
2. **Trace** — the reference code in `src/` is small, layered, and explicit enough to follow line by line.
3. **Validate** — `expected_outputs/` contains the exact outputs and artifacts each step produces, so you can check your understanding (or your own runs) against them.
4. **Rebuild** — `exercises/` gives you skeletons with TODOs; you reimplement everything from scratch and compare against `solutions/` and `expected_outputs/`.

The per-lesson loop:

```
read README  →  trace src/  →  study expected_outputs/  →  solve exercises/  →  compare with solutions/  →  rebuild from scratch
```

## Prerequisites

- Python fundamentals (functions, classes, modules, type hints).
- Basic ML vocabulary (train/test split, accuracy, overfitting).
- Git and a GitHub account (the CI/CD pipelines run on GitHub Actions).
- [uv](https://docs.astral.sh/uv/) for Python and dependency management — installation covered in `00-setup/`.

## Quickstart

```bash
git clone <your-fork-or-clone-url>
cd mlops-course
uv sync
uv run python -c "print('environment ready')"
```

Expected output of the last command:

```
environment ready
```

Full setup walkthrough, with the expected output of every command, lives in [`00-setup/README.md`](00-setup/README.md).

## Repository structure

```
mlops-course/
├── README.md                 course index (this file)
├── 00-setup/                 environment (uv), conventions, ML CI/CD pipeline landscape
├── lessons/
│   └── NN-name/              one self-contained folder per lesson
├── shared/                   common utilities + synthetic data generators
├── .github/workflows/        GitHub Actions pipelines, added lesson by lesson
├── pyproject.toml            single uv-managed environment for the whole course
├── uv.lock                   locked dependency versions — what makes expected outputs exact
└── .python-version           pinned Python version
```

## Lesson template

Every lesson under `lessons/` follows the same contract:

```
lessons/NN-name/
├── README.md            1) objectives  2) theory  3) diagrams  4) step-by-step walkthrough
│                        5) expected outputs  6) exercises  7) validation checklist
│                        8) build-from-scratch guide
├── src/                 reference implementation, layered: data / features / model / serving / pipeline
├── exercises/           skeletons with TODOs for you to fill in
├── solutions/           reference solutions to the exercises
├── expected_outputs/    exact artifacts and console outputs to validate against by hand
└── data/                local datasets, when the lesson needs them
```

## Roadmap

Lessons are generated incrementally, one at a time. Status legend: ✅ available · 🔜 next · 🔒 planned.

| NN | Lesson | What you build | Status |
|----|--------|----------------|--------|
| 00 | [Setup & the ML CI/CD pipeline landscape](00-setup/README.md) | uv environment + a mental map of every way ML pipelines get built | ✅ |
| 01 | [Churn CI/CD: training + local deployment](lessons/01-churn-ci-cd/README.md) | layered training pipeline, FastAPI local serving, first GitHub Actions workflow with a metric quality gate | ✅ |
| 02 | [Monitoring](lessons/02-monitoring/README.md) | service metrics + model metrics, structured logging, dashboard, scheduled monitoring workflow | ✅ |
| 03 | [Drift detection](lessons/03-drift-detection/README.md) | PSI from scratch, reference profiles, drift gate, `repository_dispatch` retraining trigger | ✅ |
| 04 | [Containerization + AWS Lambda](lessons/04-docker-lambda/README.md) | Lambda container image, RIE local validation, OIDC, Docker → ECR → Lambda → API Gateway pipeline | ✅ |
| 05 | [Deployment strategies](lessons/05-deployment-strategies/README.md) | blue-green / canary / shadow router, shadow comparison, promotion gate, progressive-deploy pipeline | ✅ |
| 06 | MLflow | model registry, versioning, reproducibility | 🔜 |
| 07 | Embeddings from scratch | what embeddings are, training a simple one, validating it | 🔒 |
| 08 | GANs | how GANs are built and how to deploy them | 🔒 |
| 09 | Mini-LLM from scratch | tokenizer → attention → transformer block | 🔒 |

## Code standards

All reference code, exercises, and solutions follow these rules — learn them once in `00-setup/`, then expect them everywhere:

- **No comments, no docstrings.** Code must explain itself through explicit names and small functions.
- **Single Responsibility Principle.** One module, one job. Layered architecture: `data / features / model / serving / pipeline`.
- **Dependency injection.** Collaborators are passed in as arguments; nothing instantiates its own dependencies deep inside.
- **Fail loud.** Input validation with `if` + `raise ValueError`. No defensive `try/except`.
- **uv-managed Python.** One root `pyproject.toml`; dependencies are added as lessons need them.
- **Explicit names.** `train_test_split_by_ratio`, not `split2`.

## Working protocol

The course grows one lesson at a time. Before each lesson is written, a mini-index of its contents is proposed and approved. A lesson is only considered done when its README, reference code, exercises, solutions, and expected outputs are all in place.
