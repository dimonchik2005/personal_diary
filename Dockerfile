FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.2.1

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root --no-ansi

RUN useradd --create-home appuser

COPY --chown=appuser:appuser . .

RUN mkdir -p /app/staticfiles \
    && chown -R appuser:appuser /app/staticfiles

USER appuser