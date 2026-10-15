# syntax=docker/dockerfile:1
# Versioned base images; immutable digest locking remains a separate gate.
ARG PYTHON_IMAGE=python:3.12.12-slim-bookworm
FROM ${PYTHON_IMAGE} AS base
COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /usr/local/bin/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_PROJECT_ENVIRONMENT=/opt/matchpulse-venv
WORKDIR /workspace
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM base AS development
RUN uv sync --frozen --extra dev --no-editable
COPY tests ./tests
ENV PATH="/opt/matchpulse-venv/bin:${PATH}"
CMD ["python", "-m", "pytest", "-q"]

FROM python:3.12.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/matchpulse-venv/bin:${PATH}"
WORKDIR /app
RUN useradd --create-home --uid 10001 matchpulse
COPY --from=base /opt/matchpulse-venv /opt/matchpulse-venv
USER matchpulse
CMD ["python", "-c", "from matchpulse.scenarios import scenario; from matchpulse.intelligence import analyze_stream; match, events = scenario('high_press'); print(analyze_stream(match, events))"]
