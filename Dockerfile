# ✅ Use AWS Lambda Python 3.12 base image
FROM public.ecr.aws/lambda/python:3.12

# ✅ Set the working directory to AWS Lambda's function root
WORKDIR ${LAMBDA_TASK_ROOT}

# ✅ Copy and install dependencies first (optimizes caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Copy all application files (instead of multiple COPY commands)
COPY . ${LAMBDA_TASK_ROOT}

# ✅ Ensure Lambda can execute the FastAPI handler
CMD ["main.handler"]


