# Development environments

## Business purpose

The same canonical football-intelligence package runs natively, in Docker Compose and in the production OCI image. Packaging must never change tactical inference: the same canonical event sequence must produce the same evidence-backed insight.

## Prerequisites

- Python 3.12 for the CI-equivalent native workflow.
- `uv 0.10.0`.
- Node.js 24.22.x and npm 11 for frontend development.
- Docker Desktop or a compatible Docker/Compose runtime.
- D2 v0.9.0 only when rendering architecture locally.

## Python checks

~~~sh
uv sync --frozen --extra dev
uv run --frozen bash scripts/check.sh
~~~

`scripts/check.sh` is the shared local/CI entrypoint for Pytest and Ruff.

## Frontend and generated API contracts

The backend is the transport contract source of truth. Do not hand-copy Pydantic response models into TypeScript.

~~~sh
npm ci --prefix web
uv run --frozen bash scripts/check-web.sh
~~~

`scripts/check-web.sh`:

1. exports FastAPI OpenAPI to `web/openapi.json`;
2. generates `web/src/api/generated.ts` with `openapi-typescript`;
3. fails if committed generated artifacts drift;
4. runs Biome, TypeScript, Vitest and the Vite production build.

When intentionally changing an API contract, regenerate the committed files before review:

~~~sh
uv run --frozen python scripts/export-openapi.py
npm --prefix web run contracts:generate
npm --prefix web run format
~~~

## Live development with Docker Compose

~~~sh
docker compose up --build api frontend
~~~

- FastAPI/Uvicorn: http://localhost:8000
- React/Vite: http://localhost:5173
- Vite proxies `/api` and `/health` to the API service, so development does not require a separate CORS policy.
- SSE remains same-path from the browser's perspective.

The long-lived `dev` service remains available for VS Code Dev Containers.

## Production-style runtime

~~~sh
docker build --target runtime -f docker/backend.Dockerfile -t matchpulse-runtime:test .
docker run --rm -p 8000:8000 matchpulse-runtime:test
~~~

The multi-stage build compiles React and copies the static bundle into the non-root FastAPI runtime. FastAPI serves the UI same-origin after explicit API routes. This deliberately gives the hackathon one deployable workload while keeping Python and React source boundaries separate.

## Reproducibility

- `uv.lock` fixes Python transitive versions and hashes; CI uses `uv lock --check` and `uv sync --frozen`.
- `web/package-lock.json` fixes the npm dependency graph; CI uses `npm ci`.
- Python, uv and Node container images are pinned by immutable OCI digests.
- D2 is pinned to v0.9.0 in CI.
- GitHub Action references are still version tags rather than immutable action SHAs; pinning them is a separate supply-chain hardening task.

Apple Silicon development builds ARM64 locally by default. Any eventual Azure image build must explicitly target the intended Container Apps architecture or publish a tested multi-architecture manifest.

## Implemented vs planned

Implemented locally: canonical schemas, synthetic scenarios, deterministic detectors, FastAPI/SSE, evidence HTTP API, React broadcast UI, generated transport contracts, Docker packaging and automated checks.

Planned: Foundry agent orchestration, deterministic narrative claim verification, production telemetry, Azure Container Apps deployment, persisted multi-replica state, authentication and authorized external feed adapters.

No billable Azure resource may be provisioned or modified without explicit cost review and approval.
