# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
# External OCI images are pinned by immutable multi-arch index digests.
ARG PYTHON_IMAGE=python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c
ARG NODE_IMAGE=node:24.22.0-bookworm-slim@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5

FROM ${NODE_IMAGE} AS web-development
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web ./
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM web-development AS web-builder
ARG PITCHVOLT_BUILD_SHA=local
RUN npm run build && sed -i "s/__PITCHVOLT_BUILD_SHA__/${PITCHVOLT_BUILD_SHA}/g" dist/index.html

FROM ${PYTHON_IMAGE} AS base
COPY --from=ghcr.io/astral-sh/uv:0.10.0@sha256:78a7ff97cd27b7124a5f3c2aefe146170793c56a1e03321dd31a289f6d82a04f /uv /uvx /usr/local/bin/
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

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/matchpulse-venv/bin:${PATH}" \
    MATCHPULSE_WEB_DIST=/app/web
WORKDIR /app
RUN useradd --create-home --uid 10001 matchpulse
COPY --from=base /opt/matchpulse-venv /opt/matchpulse-venv
COPY --from=web-builder /web/dist /app/web
USER matchpulse
EXPOSE 8000
CMD ["uvicorn", "matchpulse.api:app", "--host", "0.0.0.0", "--port", "8000"]
