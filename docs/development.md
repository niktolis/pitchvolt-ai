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
python -m pip install -e '.[dev]'
bash scripts/check.sh
```

## Scope and architecture
- `docker/backend.Dockerfile`: multi-stage build with separate development and non-root runtime stages.
- `compose.yaml`: local test and development services using the same image source, not extra cloud services.
- `.devcontainer/devcontainer.json`: reuse Compose rather than duplicate dependency installation.
- `scripts/check.sh`: single test/lint entrypoint for local and CI.
- Architecture rendering: `bash scripts/render-architecture.sh` on a host with D2 installed.

**Explicitly not implemented:** FastAPI ingress, frontend, streaming transport, Foundry inference, cloud provisioning, distributed state, or production liveness probes. The runtime image currently executes a CLI smoke example until an API exists.

## Reproducibility follow-up
Python is fixed to the 3.12 minor and dependency versions are bounded but not yet fully locked. Before producing deployment images, generate and commit a reproducible lock file and pin image digests. The D2 CLI version should likewise be fixed consistently across local development and CI; do not mistake this first containerized slice for fully reproducible production packaging.

For Apple Silicon development, Docker builds local ARM64 images by default; Azure deployment image builds must explicitly target `linux/amd64` or provide a multiarch manifest and be tested.
