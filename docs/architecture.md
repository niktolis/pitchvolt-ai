# PitchVolt AI — Architecture Compatibility Entry Point

The canonical architecture documentation is **[docs/architecture/README.md](architecture/README.md)**. Accepted decisions live under **[docs/decisions/](decisions/)**.

This file is intentionally short to avoid maintaining a second, contradictory architecture baseline.

## Current implementation

- Synthetic canonical football-event contracts with explicit provenance.
- Deterministic state, validation, high-press/counterattack detection and evidence.
- FastAPI HTTP/SSE replay transport with deterministic reconnect cursors.
- React/TypeScript live broadcast UI generated against the FastAPI OpenAPI contract.
- Docker Compose development and one production OCI image serving API + compiled UI.
- D2 architecture source and generated SVG documentation.

## Approved but not yet implemented

- Microsoft Foundry Analyst + Storyteller orchestration.
- Deterministic verification of model-generated narrative claims.
- Optional Editorial escalation.
- Azure Container Apps Consumption deployment, telemetry and measured production SLOs.

Do not add architectural detail here. Update the canonical D2-backed architecture pages and relevant ADRs instead.
