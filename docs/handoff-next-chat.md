# PitchVolt AI — durable handoff (18 October 2026)

**Deadline:** 27 October 2026. **Current authoritative source:** the main branch plus open GitHub issues and pull requests, not stale summaries here.

## Repository, scope and rules
- Private repository: https://github.com/niktolis/pitchvolt-ai; project: https://github.com/users/niktolis/projects/6.
- Original **fictional/synthetic football** events only. Do not import actual StatsBomb Open Data as synthetic; licensing and full historic compatibility tracked by #15.
- Canonical validated `MatchEvent` and one deterministic `MatchProcessor` own all metrics, identity, score and evidence. Agents must not fabricate football truths.
- Architecture ADRs: `docs/decisions/ADR-0001-intelligence-boundary.md`, `ADR-0002-agent-orchestration.md`, `ADR-0003-container-apps-streaming.md`. Two-speed delivery: fast deterministic match events independently of slow narrative.
- **GitHub workflow:** issue → branch → tests → draft PR → explicit owner review/approval → merge. **Do not invoke Codex commands/integrations or grant GitHub organization access without explicit prior approval** (particularly `cariad-t2`). Prior PitchVolt-specific Codex exception wording was outdated; explicit approval is required.
- **Zero out-of-pocket Azure policy:** subscription Free Trial with spending limit; project resource group `rg-matchpulse-dev`, Foundry account `matchpulse-ai-resource`, project `matchpulse-ai` in `swedencentral`. No Azure model deployment, inference invocation or billable provisioning without separately presenting model, projected costs and controls for explicit approval. Budget alerts alone are not a hard cap.
- Do not merge automatically; no external model calls during local/CI testing.

## Merged baseline
- #13: FastAPI deterministic finite SSE replay, scenarios, evidence/state API.
- #14: React/TypeScript Vite UI, pitch, timeline, audience modes, generated OpenAPI TS, container package.
- #16: strict synthetic StatsBomb-shaped adapter; 120 × 80 provider units normalized to canonical 105 × 68 metres; full historical import still pending (#15).
- #17: controlled Analyst → Storyteller `Orchestrator`, immutable evidence bundle, fail-closed typed claims and bounded server-rendered prose, optional but disabled `FoundryRoles` provider, **separate local narrative SSE**, React narrative panels and corresponding regression tests; D2 CI now triggers on PRs and main pushes (no automatic branch writes).
- #18: dedicated future UI improvements including distinct team colors, fictional crests in synthetic metadata and an accurate scoreboard. Do not broaden Foundry issue #4 to include these.

## Issue #4 — P0 remaining
- Actual Microsoft Agent Framework + Foundry project inference with reviewed/pinned dependencies and documented SDK compatibility, behind approved cost gate.
- Typed/provenance-checked, generated narrative transport contracts, resilient cancellation/timeouts/stale response handling.
- Genuine evidence tool calls and agent handoff traces; always-on deterministic verifier; optional Editorial only if uncertainty justifies.
- Single-agent comparison, real p50/p95 model latency, token usage and cost per scenario after owner-approved deployment.
- Synchronize documentation and architecture diagrams, proof for `docs/judging-traceability.md`, and evaluate hackathon criteria.

## Source entry points
- `src/pitchvolt/events.py`, `intelligence.py`, `scenarios.py`, `narrative.py`, `workflow.py`, `narrative_stream.py`, `foundry_adapter.py`, `api.py`
- `web/src/App.tsx`, `web/src/api/client.ts`
- `docs/architecture/README.md`, `docs/architecture/controlled-narratives.md`, `docs/architecture/narrative-stream.md`
- Local checks: `uv sync --frozen --extra dev && uv run --frozen bash scripts/check.sh`; `npm ci --prefix web && uv run --frozen bash scripts/check-web.sh`; `docker compose up --build api frontend`.
- Architecture: D2 in `docs/architecture/diagrams`, generated SVGs in `docs/architecture/rendered`; CI publishes PDF/PPTX artifact.

Always verify issue/PR status in GitHub before continuing.

## Repository identity migration (18 October 2026)

The authoritative product name is **PitchVolt AI**, GitHub target
`niktolis/pitchvolt-ai`, Python package `pitchvolt`, npm package
`pitchvolt-web`, and new narrative runtime variable
`PITCHVOLT_NARRATIVE_PROVIDER`. See [GitHub and Entra OIDC cutover
runbook](repository-rename.md). Existing Azure resources retain their original
physical identifiers until a separate authorized migration. Avoid assuming
that changing a source-code string renames any Azure resource.
