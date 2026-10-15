# MatchPulse AI

Real-time, explainable football intelligence and personalized storytelling for the Microsoft Premier League AI Hackathon.

MatchPulse AI deliberately separates **football truth** from **AI explanation**:

**Ingest → Interpret → Explain → Render → Personalize**

- Synthetic, fictional match events are validated through canonical Pydantic schemas.
- Deterministic match logic owns possession, tactical detection, metrics, provenance and evidence.
- FastAPI publishes replayable Server-Sent Events and immutable evidence endpoints.
- React renders a live 105 × 68m pitch, event replay, tactical insights and evidence inspection.
- Audience modes change presentation while preserving the same verified facts.
- Microsoft Foundry Analyst/Storyteller orchestration is the next implementation milestone; it must consume evidence and pass deterministic claim verification.

No unauthorized Premier League event data or footage is used.

## Current implementation

The repository currently implements:

- canonical versioned football-event models and validation;
- deterministic fictional scenarios for high press, counterattack and a sustained-possession negative control;
- deterministic high-press/counterattack detection with stable source-event IDs;
- replayable FastAPI/SSE transport with reconnect cursor support;
- evidence and state HTTP endpoints;
- React/TypeScript live broadcast UI with pitch, timeline, evidence inspection and casual/analyst/club views;
- generated TypeScript API contracts from FastAPI OpenAPI;
- reproducible Python and npm dependency locks;
- Docker Compose development and a single production OCI runtime containing FastAPI plus compiled React;
- D2 architecture sources with generated Markdown renders;
- CI for Python, frontend contracts/builds and architecture rendering.

**Not yet implemented:** Microsoft Foundry inference/orchestration, deterministic narrative claim verification, Azure deployment, production telemetry/latency measurements, authentication, persisted live-feed state, multilingual recap.

## Run locally

### Docker Compose development

~~~sh
docker compose up --build api frontend
~~~

Open http://localhost:5173. Vite proxies API and SSE traffic to FastAPI.

### Native checks

~~~sh
uv sync --frozen --extra dev
uv run --frozen bash scripts/check.sh

npm ci --prefix web
uv run --frozen bash scripts/check-web.sh
~~~

### Production-style single container

~~~sh
docker build --target runtime -f docker/backend.Dockerfile -t matchpulse-ai .
docker run --rm -p 8000:8000 matchpulse-ai
~~~

Open http://localhost:8000.

## Architecture and business logic

Start with [docs/architecture/README.md](docs/architecture/README.md).

- [Tactical business logic](docs/architecture/business-logic.md)
- [Real-time API](docs/architecture/realtime-api.md)
- [Live broadcast UI](docs/architecture/frontend.md)
- [Accepted architecture decisions](docs/decisions/)
- [Development workflow](docs/development.md)
- [Judging traceability](docs/judging-traceability.md)

## Cost and deployment guardrail

Azure Container Apps Consumption is the approved deployment target, but no Azure resource may be provisioned or changed without an explicit cost review and project-owner approval. The project has a strict zero-out-of-pocket requirement.
