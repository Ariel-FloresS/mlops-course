# Exercises — Lesson 04

Same loop as always: implement, swap into place, validate, restore with git, compare with `../solutions/`.

All commands run from `lessons/04-docker-lambda/`.

| # | Skeleton | Replaces | Validate with | Expected |
|---|----------|----------|---------------|----------|
| 1 | `exercise_1_lambda_handler.py` | `src/serving/lambda_handler.py` | `uv run pytest -q` | `7 passed` |
| 2 | `exercise_2_dockerfile` | `Dockerfile` | `docker build -t churn-lambda:exercise .` then the RIE curl | responses match `expected_outputs/rie_invocation.txt` |
| 3 | (you create the files) | — | see below | responses match `solutions/solution_3_events/expected_responses.txt` |
| 4 | `exercise_4_workflow.yml` | `.github/workflows/04-deploy-lambda.yml` | diff vs solution, then a PR run | run matches `expected_outputs/workflow_run_summary.txt` |

Example, exercise 1:

```bash
cp exercises/exercise_1_lambda_handler.py src/serving/lambda_handler.py
uv run pytest -q
git checkout -- src/serving/lambda_handler.py
```

## Exercise 3 — craft the events

Write three API Gateway HTTP API (payload v2) event files from scratch, without looking at `events/`:

- **a)** a request whose body is **base64-encoded** (`isBase64Encoded: true`) for the low-risk customer profile — must return 200 with `churn_label` 0;
- **b)** a request missing the `support_tickets` field — must return 422 with `loc: ["support_tickets"]`;
- **c)** an event whose `body` is `null` — must return 400 with the exact error message.

Validate without Docker (after training in walkthrough step 2):

```bash
uv run python -c "
import json
from src.serving.lambda_handler import MODEL_PATH, get_model_pipeline, respond_to_event
event = json.loads(open('my_event_a.json').read())
print(json.dumps(respond_to_event(get_model_pipeline(MODEL_PATH), event)))
"
```

Compare with `solutions/solution_3_events/` (three reference events + their exact responses). With Docker available, the RIE curl validates the same files end to end.
