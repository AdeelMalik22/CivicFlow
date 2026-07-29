# syntax=docker/dockerfile:1
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN addgroup --system civicflow \
    && adduser --system --ingroup civicflow civicflow

COPY pyproject.toml README.md ./
COPY civicflow ./civicflow
COPY apps ./apps
RUN python -m pip install --no-cache-dir .

COPY manage.py ./
COPY templates ./templates
COPY static ./static

RUN DJANGO_SETTINGS_MODULE=civicflow.settings.test \
    python manage.py collectstatic --noinput \
    && chown -R civicflow:civicflow /app

USER civicflow

EXPOSE 8000

CMD ["uvicorn", "civicflow.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
