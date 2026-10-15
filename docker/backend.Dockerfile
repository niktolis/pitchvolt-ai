# syntax=docker/dockerfile:1
ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE} AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

FROM base AS development
RUN python -m pip install --no-cache-dir '.[dev]'
COPY tests ./tests
CMD ["python", "-m", "pytest", "-q"]

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --create-home --uid 10001 matchpulse
COPY --from=base /usr/local /usr/local
USER matchpulse
# The current library has no network server, so no port or healthcheck is asserted.
CMD ["python", "-c", "from matchpulse.scenarios import scenario; from matchpulse.intelligence import analyze_stream; match, events = scenario('high_press'); print(analyze_stream(match, events))"]
