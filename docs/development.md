# Development environments

## Business purpose
The same canonical football intelligence Python package runs natively, in local Docker Compose, and eventually in a Container Apps OCI runtime. Containers do not change tactical inference: a press, turnover, carry, pass and shot still yield a single evidence-backed high-press insight.

## Local development (macOS / fish compatible)
Install Docker Desktop (or a compatible Compose runtime), and from repository root:

```sh
docker compose build backend
docker compose run --rm backend bash scripts/check.sh
docker compose run --rm backend python -c "from matchpulse.scenarios import scenario; from matchpulse.intelligence import analyze_stream; m, e = scenario('high_press'); print(analyze_stream(m, e))"
```

Open the repository with VS Code **Dev Containers: Reopen in Container** to work in the long-lived Compose `dev` service.

Native Python is equally supported:

```sh
uv sync --frozen --extra dev
uv run --frozen bash scripts/check.sh
```

## Scope and architecture
- `docker/backend.Dockerfile`: multi-stage build with separate development and non-root runtime stages.
- `compose.yaml`: local test and development services using the same image source, not extra cloud services.
- `.devcontainer/devcontainer.json`: reuse Compose rather than duplicate dependency installation.
- `scripts/check.sh`: single test/lint entrypoint for local and CI.
- Architecture rendering: `bash scripts/render-architecture.sh` on a host with D2 installed.

**Explicitly not implemented:** FastAPI ingress, frontend, streaming transport, Foundry inference, cloud provisioning, distributed state, or production liveness probes. The runtime image currently executes a CLI smoke example until an API exists.

## Reproducibility follow-up
The committed `uv.lock` fixes Python transitive dependency versions and distribution hashes; `uv lock --check` is mandatory in CI, and Docker uses `uv sync --frozen`. The package requires Python 3.11+ and CI exercises Python 3.12. The OCI base image and uv tool-image digest locking is tracked as a separate explicit supply-chain gate; floating image digests still prevent claiming fully reproducible container builds. D2 renderer version is pinned to `v0.9.0` in CI and verified in `scripts/render-architecture.sh`. Install that D2 version locally with the official installer (`--version v0.9.0`) when necessary.

For Apple Silicon development, Docker builds local ARM64 images by default; Azure deployment image builds must explicitly target `linux/amd64` or provide a multiarch manifest and be tested.
