# AWS setup — one time, by hand

Everything the pipeline needs on the AWS side, created once from your terminal. Prerequisites: an AWS account, the AWS CLI v2 authenticated with a user/role that can administer IAM, ECR, Lambda, and API Gateway, and Docker running locally for the first image push.

Outputs below are **shape references**: structure and key fields are exact; account ids, ARNs, digests, and timestamps will be yours. `123456789012` stands for your account id everywhere.

## 0. Variables used by every step

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo $AWS_ACCOUNT_ID
```

Expected output: your 12-digit account id.

## 1. ECR repository

```bash
aws ecr create-repository --repository-name churn-lambda --region $AWS_REGION
```

Expected output (shape):

```json
{
    "repository": {
        "repositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/churn-lambda",
        "repositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/churn-lambda",
        "imageTagMutability": "MUTABLE"
    }
}
```

## 2. GitHub OIDC identity provider (one per AWS account)

This is what lets the workflow get temporary credentials with **no stored access keys**: GitHub signs a token per run; AWS verifies it and exchanges it for a short-lived role session.

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

Expected output: `{ "OpenIDConnectProviderArn": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com" }`

If it already exists you get `EntityAlreadyExists` — that is a pass. (AWS now validates GitHub's certificate chain directly; the thumbprint remains a required parameter.)

## 3. The deploy role and its trust policy

`trust-policy.json` — read the `Condition` carefully, it is the security boundary. Only workflow runs **from this repo, on the `main` ref** can assume the role; a fork or a PR branch cannot:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:<YOUR_GITHUB_USER>/mlops-course:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

```bash
aws iam create-role \
  --role-name github-actions-churn-deployer \
  --assume-role-policy-document file://trust-policy.json
```

Expected output: JSON containing `"Arn": "arn:aws:iam::123456789012:role/github-actions-churn-deployer"` — **this is the value for the `AWS_DEPLOY_ROLE_ARN` GitHub variable.**

`permissions-policy.json` — least privilege: push to ONE repo, update ONE function:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "ecr:GetAuthorizationToken",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Resource": "arn:aws:ecr:us-east-1:123456789012:repository/churn-lambda"
    },
    {
      "Effect": "Allow",
      "Action": ["lambda:UpdateFunctionCode", "lambda:GetFunction"],
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:churn-predictor"
    }
  ]
}
```

```bash
aws iam put-role-policy \
  --role-name github-actions-churn-deployer \
  --policy-name churn-deploy-permissions \
  --policy-document file://permissions-policy.json
```

Expected output: none (silence is a pass).

## 4. Lambda execution role (the function's own identity, distinct from the deploy role)

```bash
aws iam create-role \
  --role-name churn-lambda-execution \
  --assume-role-policy-document '{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
aws iam attach-role-policy \
  --role-name churn-lambda-execution \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

Expected output: role JSON, then silence.

## 5. First image push (the function cannot be created without an image)

From `lessons/04-docker-lambda/` with a trained `artifacts/` (walkthrough steps 2–3):

```bash
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker build -t churn-lambda:bootstrap .
docker tag churn-lambda:bootstrap $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/churn-lambda:bootstrap
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/churn-lambda:bootstrap
```

Expected output: `Login Succeeded`, the build log, then layer pushes ending in `bootstrap: digest: sha256:<digest> size: <n>`.

## 6. The Lambda function

Memory and timeout matter: importing scikit-learn + pandas on cold start needs both.

```bash
aws lambda create-function \
  --function-name churn-predictor \
  --package-type Image \
  --code ImageUri=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/churn-lambda:bootstrap \
  --role arn:aws:iam::$AWS_ACCOUNT_ID:role/churn-lambda-execution \
  --memory-size 1024 \
  --timeout 30
aws lambda wait function-active --function-name churn-predictor
```

Expected output: function JSON with `"State": "Pending"`, then silence when active.

## 7. API Gateway (HTTP API, quick-create)

```bash
aws apigatewayv2 create-api \
  --name churn-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:churn-predictor
```

Expected output (shape): JSON containing `"ApiEndpoint": "https://<api-id>.execute-api.us-east-1.amazonaws.com"` — **this is the value for the `API_GATEWAY_URL` GitHub variable.**

Allow the API to invoke the function:

```bash
aws lambda add-permission \
  --function-name churn-predictor \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$AWS_REGION:$AWS_ACCOUNT_ID:<api-id>/*"
```

Quick-create wires a `$default` route: every path and method reaches the function — which is fine, because the handler is deliberately route-agnostic (API Gateway owns routing; the handler owns one job).

## 8. GitHub repository variables

Repo → Settings → Secrets and variables → Actions → **Variables** (not secrets — none of these values is sensitive; the OIDC trust policy is the credential):

| Variable | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | the role ARN from step 3 |
| `AWS_REGION` | e.g. `us-east-1` |
| `ECR_REPOSITORY` | `churn-lambda` |
| `LAMBDA_FUNCTION_NAME` | `churn-predictor` |
| `API_GATEWAY_URL` | the ApiEndpoint from step 7 |

The deploy job is guarded by `vars.AWS_DEPLOY_ROLE_ARN != ''` — until you set these, the pipeline stays green with deploy skipped.

## 9. End-to-end check

```bash
curl -fsS -X POST "$API_GATEWAY_URL/predict" \
  -H "Content-Type: application/json" \
  -d '{"tenure_months": 2, "monthly_charges": 95.0, "total_charges": 190.0, "contract_type": "month_to_month", "payment_method": "electronic_check", "support_tickets": 4}'
```

Expected output — exact, because the model in the image is deterministic:

```
{"churn_probability": 0.9966, "churn_label": 1}
```

(First call after a deploy or idle period takes seconds — cold start. Repeat it and watch it drop to milliseconds.)

Note the response here is the **body only**: API Gateway consumed the `statusCode`/`headers` envelope your handler returned and turned it into the actual HTTP response — compare with the raw envelope the RIE showed you locally.
