# 04 — Containerization + AWS Lambda: Docker → ECR → Lambda → API Gateway

Three lessons of serving have lived on `127.0.0.1`. This lesson packages the model service into a **container image** — the artifact to end all artifacts: code, dependencies, *and* the trained model, frozen into one immutable, digest-addressed unit — and ships it through the canonical serverless path: **ECR** (the image registry) → **Lambda** (runs the container per request) → **API Gateway** (the public HTTP door). The pipeline gets AWS credentials via **OIDC**, with zero stored secrets.

Two honest framings up front. First: you can do ~80% of this lesson **without an AWS account** — the AWS base image ships with the Lambda **Runtime Interface Emulator**, so the exact image you would deploy runs and answers on your laptop. Second: the serving layer is *swapped*, not extended — the FastAPI app from lessons 01–03 is replaced by a 70-line Lambda handler, and everything below it (`model/`, `schemas`) survives untouched. That survival is the layered architecture paying rent.

---

## 1. Objectives

After this lesson you can:

- Explain why a container image is the strongest artifact format: build-once/promote-many made literal, with the model baked in.
- Write a Lambda container image: AWS base image, pinned runtime-only dependencies, layer-cache-aware ordering, dotted-path `CMD`.
- Write a native Lambda handler for API Gateway proxy events — parsing, base64, validation-to-status-code translation — and say precisely why it may use two narrow `try/except` blocks when course code otherwise never does.
- Validate the deployable image locally with the Runtime Interface Emulator, no AWS account involved.
- Explain the OIDC handshake (GitHub run token → STS → short-lived role session) and the trust-policy condition that scopes it to one repo and one ref.
- Read the full deploy pipeline: test → build + RIE smoke test → (conditional) push to ECR, update Lambda, remote smoke test.

---

## 2. Theory

### 2.1 The image is the artifact

Lesson 01 produced `model.joblib` + `metrics.json` and called it the artifact. It had a hidden dependency: whoever loads it must have the *right* Python, the *right* scikit-learn, the *right* platform. The container image closes that hole by freezing all three layers together:

```
image = OS + Python runtime + pinned libraries + src/ + artifacts/model.joblib
```

Properties that matter operationally:

- **Immutable and content-addressed.** A pushed image has a digest (`sha256:…`). Deploying digest X today and digest X next month is *provably* the same service. Rollback = point back at the old digest.
- **Build once, promote many — literally.** Lesson 00 §2.4 promised it; here the *same bytes* move laptop → CI smoke test → ECR → Lambda. Nothing is rebuilt between environments after the push. (Within the workflow, the PR job and the deploy job each build — the promoted unit is the image *from the push onward*; lesson 05 leans on exactly that digest for deployment strategies.)
- **The model rides inside.** Alternative: image without model, download from storage at cold start. That buys smaller images and independent model updates, at the cost of a *mutable* deployment (same image, different behavior — the digest guarantee dies). For a single small model, baked-in wins; we name the trade-off and move on.

### 2.2 Anatomy of the Dockerfile

```dockerfile
FROM public.ecr.aws/lambda/python:3.12

COPY requirements-lambda.txt ${LAMBDA_TASK_ROOT}/requirements-lambda.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements-lambda.txt

COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY artifacts/ ${LAMBDA_TASK_ROOT}/artifacts/

CMD ["src.serving.lambda_handler.handler"]
```

Line by line, the decisions:

- **The AWS base image** brings the Lambda Runtime API plumbing, a matching Python 3.12, and the RIE for local runs. `LAMBDA_TASK_ROOT` (`/var/task`) is where Lambda expects code; it is also the working directory, which is why the handler's relative `artifacts/model.joblib` path works unchanged locally and in the cloud.
- **`requirements-lambda.txt` is not `pyproject.toml`.** Runtime needs five packages (`pandas`, `scikit-learn`, `joblib`, `pydantic`, `numpy`) — no FastAPI, no uvicorn, no pytest. Versions are pinned to the exact `uv.lock` versions, so the container model behaves byte-identically to your local one. Dev-deps ⊃ runtime-deps is a deliberate, visible split.
- **Dependencies before code.** Docker caches layers top-down; the expensive `pip install` layer survives every code/model change and rebuilds only when the requirements file changes. Watch it happen: second build shows `CACHED` on steps 2–3 (`expected_outputs/docker_build_log.txt`).
- **`CMD` is a dotted path to a function**, not a server command. There is no web server in this image — that is the next section's point.

### 2.3 The handler replaces the framework — and inherits its duties

Lambda's model: API Gateway turns an HTTP request into a JSON **event**, calls `handler(event, context)`, and turns the returned `{statusCode, headers, body}` envelope back into an HTTP response. uvicorn and FastAPI have no role; routing belongs to API Gateway; the handler does exactly one job.

That role-shift settles a standards question. Course code never writes defensive `try/except` — but `respond_to_event` contains two `except` blocks. They are not defensive; they are **boundary translation**, the work FastAPI was doing for us all along: in lessons 01–03, pydantic's `ValidationError` became a 422 because the *framework* caught it. Now we are the framework, so the handler catches exactly two anticipated client errors and maps them to statuses:

```
bad envelope / malformed JSON  →  ValueError        →  400
schema-invalid payload         →  ValidationError   →  422
anything else                  →  uncaught          →  Lambda reports a function error (API Gateway: 502)
```

The third line is the standard surviving: unexpected failures still crash loudly. Note the symmetry with every gate in this course — *anticipated* bad input gets a typed response at the boundary; *unanticipated* bugs propagate.

Two more Lambda-specific moves in the handler:

- **`@cache` on `get_model_pipeline`** — the model loads once per container, not once per request. Lambda freezes and reuses containers between invocations ("warm starts"); the first invocation pays the import + load cost (the **cold start** you will measure with your own curl). Module-level eager loading would also work in Lambda but would break `pytest` collection before training — the cached function keeps tests injectable (`respond_to_event(tiny_model, event)`) with zero monkeypatching.
- **`isBase64Encoded` handling** — API Gateway delivers binary-ish bodies base64-encoded; a handler that ignores the flag works in tests and fails in production.

### 2.4 OIDC: deploy credentials with no stored secrets

The anti-pattern: create an IAM user, put `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` in GitHub secrets. Those keys are long-lived, leakable, rotated never.

The OIDC pattern, end to end:

1. The workflow job requests an identity token from GitHub (`permissions: id-token: write` — that line is the *permission to mint the token*).
2. The token states, signed by GitHub: "this run is repo `X`, ref `Y`".
3. `configure-aws-credentials` sends it to AWS STS: `AssumeRoleWithWebIdentity`.
4. AWS verifies the signature against the GitHub OIDC provider you registered once, checks the **trust policy condition** — `sub` must equal `repo:<you>/mlops-course:ref:refs/heads/main` — and returns credentials valid for ~1 hour.

Nothing long-lived exists. A fork, a PR branch, a stolen workflow file: none can assume the role, because the `sub` claim won't match. The trust policy *is* the credential — which is why `docs/aws_setup.md` walks its JSON line by line, and why the role's permissions policy grants exactly two capabilities (push to one ECR repo, update one function).

### 2.5 The path, and who owns what

```
docker build → ECR (stores images) → Lambda (runs one container per concurrent request) → API Gateway (HTTP, routing, throttling)
```

Division of labor worth internalizing: API Gateway owns routes and HTTP; Lambda owns scaling (zero management, but cold starts and a 1,024 MB / 30 s budget we set explicitly because pandas + sklearn need it); the image owns behavior. The deploy verb is tiny — `aws lambda update-function-code --image-uri …` — because all the real content shipped when the image was pushed. Compare with lesson 01's "deploy" (run uvicorn): same artifact-then-process pattern, different infrastructure owner.

---

## 3. Diagrams

### 3.1 The artifact's journey (build once, promote many)

```
lessons/04-docker-lambda/                      GitHub Actions runner
  src/ + artifacts/model.joblib                ┌──────────────────────────────┐
  + requirements-lambda.txt                    │ docker build                 │
  + Dockerfile ───────────────────────────────►│ churn-lambda:<git-sha>       │
                                               │   │                          │
                                               │   ▼                          │
                                               │ RIE smoke test (no AWS)      │
                                               │ curl → statusCode 200,       │
                                               │ probability 0.9966 exact     │
                                               └───┬──────────────────────────┘
                                                   │ docker push  (main only, OIDC)
                                                   ▼
                              ECR: 123456789012.dkr.ecr.…/churn-lambda:<git-sha>
                                                   │ sha256 digest — THE artifact
                                                   ▼
                              aws lambda update-function-code --image-uri …
                                                   │
                                                   ▼
                              Lambda function churn-predictor (1024 MB, 30 s)
                                                   │
                                                   ▼
                              API Gateway https://<api-id>.execute-api…
```

### 3.2 One request, end to end

```
client                API Gateway                Lambda                    handler (your code)
  │  POST /predict        │                         │                          │
  ├──────────────────────►│  HTTP → event JSON      │                          │
  │                       ├────────────────────────►│  cold? start container,  │
  │                       │                         │  import, load model once │
  │                       │                         ├─────────────────────────►│ parse_event_body
  │                       │                         │                          │   400 on bad envelope
  │                       │                         │                          │ ChurnPredictionRequest
  │                       │                         │                          │   422 on bad schema
  │                       │                         │                          │ predict_proba → round
  │                       │                         │◄─────────────────────────┤ {statusCode, headers, body}
  │                       │◄────────────────────────┤  envelope                │
  │◄──────────────────────┤  envelope → HTTP        │                          │
  │  200 {"churn_probability": 0.9966, ...}         │                          │
```

The same diagram with the RIE: replace API Gateway with `curl localhost:9000/2015-03-31/functions/function/invocations` — and note you then see the **raw envelope**, because nobody unwraps it for you. Comparing those two outputs teaches who does what.

### 3.3 The OIDC handshake

```
GitHub Actions job (deploy)                         AWS
┌─────────────────────────────┐                     ┌─────────────────────────────────┐
│ permissions: id-token: write│                     │ IAM OIDC provider               │
│        │                    │                     │  token.actions.githubuser…      │
│        ▼                    │   signed JWT        │        │ verifies signature      │
│ GitHub mints token:         │   "repo=…/mlops-    │        ▼                        │
│  sub = repo:<you>/mlops-    ├────course,ref=main"►│ trust policy check:             │
│  course:ref:refs/heads/main │                     │  sub == repo:<you>/mlops-course │
│        │                    │                     │         :ref:refs/heads/main ?  │
│        ▼                    │   ~1h credentials   │        │ yes                     │
│ configure-aws-credentials   │◄────────────────────┤ STS AssumeRoleWithWebIdentity   │
│ → docker push, update code  │                     │ role: github-actions-churn-     │
└─────────────────────────────┘                     │       deployer (2 permissions)  │
   no key stored anywhere                           └─────────────────────────────────┘
```

---

## 4. Walkthrough

All commands run from `lessons/04-docker-lambda/`. Steps 1–3 need no Docker and no AWS; step 4 needs Docker; steps 5–6 are the cloud half.

### Step 1 — run the tests

```bash
uv run pytest -q
```

Expected output:

```
.......                                                                  [100%]
7 passed in 11.16s
```

Read `tests/test_lambda_handler.py` before moving on: every test calls `respond_to_event` with an **injected** tiny model and plain event dicts — no Lambda, no Docker, no HTTP. The handler is just a function; that is the whole testability argument of §2.3.

### Step 2 — train (the model that gets baked in)

```bash
uv run python -m src.pipeline.train_pipeline
```

Expected output: identical to every previous lesson, ending `roc_auc: 0.9222 … artifacts written to artifacts/`.

### Step 3 — invoke the handler directly (no container yet)

The committed `events/` files are real API Gateway payload-v2 events. Drive the handler with them:

```bash
uv run python -c "
import json
from src.serving.lambda_handler import MODEL_PATH, get_model_pipeline, respond_to_event
for event_file in ('predict_high_risk.json', 'predict_low_risk.json', 'predict_invalid_contract.json'):
    event = json.loads(open(f'events/{event_file}').read())
    print(json.dumps(respond_to_event(get_model_pipeline(MODEL_PATH), event)))
"
```

Expected output — exact (`expected_outputs/handler_responses.txt`):

```
{"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": "{\"churn_probability\": 0.9966, \"churn_label\": 1}"}
{"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": "{\"churn_probability\": 0.0029, \"churn_label\": 0}"}
{"statusCode": 422, "headers": {"Content-Type": "application/json"}, "body": "{\"detail\": [{\"type\": \"literal_error\", \"loc\": [\"contract_type\"], \"msg\": \"Input should be 'month_to_month', 'one_year' or 'two_year'\", \"input\": \"weekly\", \"ctx\": {\"expected\": \"'month_to_month', 'one_year' or 'two_year'\"}}]}"
```

Same probabilities as lessons 01–03 — same artifact, third serving transport. Note the envelope: `body` is a JSON *string*, statusCode is data, not protocol. You are looking at what API Gateway consumes.

### Step 4 — build the image and run it with the RIE (requires Docker)

```bash
docker build -t churn-lambda:local .
```

Expected output shape — step order exact, timings/digests yours (`expected_outputs/docker_build_log.txt`). Then run it; the base image's entrypoint starts the **Runtime Interface Emulator** automatically when there's no real Lambda around:

```bash
docker run --rm -p 9000:8080 churn-lambda:local
```

Second terminal — the RIE speaks the Lambda Invoke API:

```bash
curl -fsS -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d @events/predict_high_risk.json
```

Expected output: **byte-identical to step 3's first line** (full transcript: `expected_outputs/rie_invocation.txt`). Same handler, same model, now inside the deployable image. Feel the first call lag — that is a cold start; the second call is instant. Repeat for the other two events, then rebuild (`docker build …` again) and watch steps 2–3 report `CACHED`.

> Environment note: these docker outputs are labeled *shape* because the reference transcripts could not be regenerated inside the course-authoring sandbox (its egress proxy blocks ECR's data endpoints). The response **bodies are exact** — they are the handler's deterministic output — and the CI job runs this exact build + curl for real on every PR, asserting `statusCode 200` and the 0.9966 probability.

### Step 5 — the AWS half (one-time, optional until you have an account)

Work through [`docs/aws_setup.md`](docs/aws_setup.md): ECR repo → OIDC provider → deploy role (trust policy + 2-permission policy) → Lambda execution role → bootstrap push → `create-function` (1024 MB / 30 s) → API Gateway quick-create → five GitHub **variables**. Every command ships with its expected output shape. The finale is the cloud smoke test:

```bash
curl -fsS -X POST "$API_GATEWAY_URL/predict" -H "Content-Type: application/json" \
  -d '{"tenure_months": 2, "monthly_charges": 95.0, "total_charges": 190.0, "contract_type": "month_to_month", "payment_method": "electronic_check", "support_tickets": 4}'
```

Expected output — exact: `{"churn_probability": 0.9966, "churn_label": 1}`. Body only: API Gateway unwrapped the envelope the RIE showed you raw.

### Step 6 — read the pipeline, then watch it

`.github/workflows/04-deploy-lambda.yml`, mapped to the theory:

- Job `test` — the handler suite, model injected, no infra.
- Job `build-and-smoke-test` — train → `docker build` → run the container → curl the RIE → `grep -F` asserts on `"statusCode": 200` **and** the exact probability. The deployable artifact is functionally verified on every PR, before any cloud exists.
- Job `deploy` — guarded twice: `github.ref == 'refs/heads/main'` and `vars.AWS_DEPLOY_ROLE_ARN != ''` (grey/skipped until you finish step 5 — a green pipeline with deploy skipped is the *designed* pre-AWS state). Inside: OIDC assume-role (`permissions: id-token: write`), ECR login, tag + push by git SHA, `update-function-code`, `wait function-updated`, remote curl asserting the same exact probability.

Compare your run with `expected_outputs/workflow_run_summary.txt`, including the three failure modes documented there.

---

## 5. Expected outputs — file map

| File | Produced by | Exact or shape |
|---|---|---|
| `pytest_output.txt` | `uv run pytest -q` | exact (duration varies) |
| `train_log.txt` | step 2 | exact |
| `handler_responses.txt` | step 3 | **exact** |
| `docker_build_log.txt` | step 4 build | shape (order exact; timings/digests vary) |
| `rie_invocation.txt` | step 4 curls | bodies **exact**; transport lines shape |
| `workflow_run_summary.txt` | reading the Actions run | states + assertions exact |
| `solutions/solution_3_events/expected_responses.txt` | exercise 3 validation | **exact** |
| AWS command outputs | `docs/aws_setup.md` inline | shape (ARNs/ids are yours) |

The pattern to notice: everything derived from the model is exact everywhere — laptop, container, CI, Lambda. Everything derived from infrastructure (timings, digests, ids) varies. Determinism follows the artifact.

---

## 6. Exercises

Skeletons in `exercises/`, answers in `solutions/`, loop in `exercises/README.md`.

1. **The handler** (`exercise_1_lambda_handler.py`) — implement `parse_event_body`, `build_response`, `respond_to_event` (the two-translation boundary). Valid: `uv run pytest -q` → `7 passed`.
2. **The Dockerfile** (`exercise_2_dockerfile`) — base image, dependency-first ordering, code + model copy, dotted CMD. Valid: build + RIE curls reproduce `rie_invocation.txt` (or diff against `solution_2_dockerfile`).
3. **Craft the events** — write three payload-v2 events from scratch (base64 200, missing-field 422, null-body 400) and validate them against exact expected responses without any infrastructure.
4. **The workflow** (`exercise_4_workflow.yml`) — rebuild the RIE smoke job and the double-guarded OIDC deploy job from memory.

---

## 7. Validation checklist

- [ ] `uv run pytest -q` prints `7 passed`, and I can explain why these tests need neither Docker nor artifacts.
- [ ] Step 3 reproduces `handler_responses.txt` byte for byte.
- [ ] I can recite the two `except` blocks in the handler, what each maps to (400 / 422), and why an unexpected bug still crashes loudly.
- [ ] (With Docker) the RIE curl matches step 3's output exactly, and I observed the cold start and the rebuild layer-cache (`CACHED` on the pip layer).
- [ ] I can explain `@cache` on the model loader in terms of cold/warm starts *and* test injectability.
- [ ] I can draw the OIDC handshake and point at: the `id-token: write` line, the `sub` condition, and why a fork cannot deploy.
- [ ] I know why the deploy job is skipped on PRs and on repos without the AWS variables — and why that is a feature.
- [ ] I can name what API Gateway consumed when comparing the RIE response with the API Gateway response.

---

## 8. Build from scratch

Keep `tests/`, `events/`, and the expected outputs as your harness; platform layers carry over.

1. **`src/serving/lambda_handler.py`** — done: `uv run pytest -q` → `7 passed`, then step 3 reproduces `handler_responses.txt`.
2. **`requirements-lambda.txt`** — from `uv.lock`, runtime-only, pinned. Done: you can justify every line and every absence (why no fastapi? why no pytest?).
3. **`Dockerfile`** — done: build succeeds; RIE curls match; second build shows `CACHED` on the dependency layer.
4. **`events/`** — done: three files drive the handler to 200/200/422 with exact outputs.
5. **`.github/workflows/04-deploy-lambda.yml`** — done: PR run green with deploy skipped; assertions in the smoke step are exact-value, not just status.
6. **`docs/aws_setup.md` execution** (when you have an account) — done: step 9's curl returns the exact body, and a push to `main` redeploys without you touching AWS again.

Stuck? The failing test and the expected output are the spec — not `src/`.

---

## Lesson summary

- A container image is the complete artifact — runtime, dependencies, code, and trained model under one immutable digest — which makes build-once/promote-many literal: the bytes you RIE-test on a laptop are the bytes Lambda runs.
- The Lambda handler replaces FastAPI and inherits its boundary duties: two narrow exception translations (400/422) at the edge, `@cache` for one model load per container, unexpected bugs still crashing loudly — same artifact, third transport, identical 0.9966.
- The deploy pipeline needs no stored cloud secrets: GitHub mints a signed per-run token, AWS's trust policy admits exactly `repo:you/mlops-course:ref:refs/heads/main`, and the deploy job stays politely skipped until the AWS variables exist.

**Next — Lesson 05 (Deployment strategies):** `update-function-code` just replaced 100% of production in one shot. If that model had been subtly broken, every user would have met it at once. Blue-green, canary, and shadow deployments fix exactly that — using Lambda aliases and weighted routing on the image digests this lesson taught you to publish.
