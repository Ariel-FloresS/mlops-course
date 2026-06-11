FROM public.ecr.aws/lambda/python:3.12

COPY requirements-lambda.txt ${LAMBDA_TASK_ROOT}/requirements-lambda.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements-lambda.txt

COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY artifacts/ ${LAMBDA_TASK_ROOT}/artifacts/

CMD ["src.serving.lambda_handler.handler"]
