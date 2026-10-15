# MatchPulse AI — Architecture Baseline

Status: **Proposed / pending review**. Owner-approved direction: deterministic football intelligence with agent-orchestrated explanation and personalization.

## Goal
Deliver an end-to-end synthetic match intelligence demonstration: **Ingest → Interpret → Explain → Render → Personalize**, targeting the hackathon's five equally weighted judging categories.

## Architectural boundaries
1. **Input adapters** accept original synthetic replay events. A future StatsBomb-shaped adapter is optional and must not couple the core to provider fields. Do not ingest/redistribute real Premier League match data.
2. **Canonical, versioned event schema** (Python / Pydantic): match identity, event identity/sequence, match clock, team/player, event type, positions, outcome, possession/context, generator provenance, schema version. Separate raw events from derived metrics and verified insight evidence.
3. **Deterministic match state and tactical detectors**: possession, sequence integrity, pass completion, pressure/turnover, shots, pressing patterns, momentum evidence. Output structured InsightCandidate with source event IDs, reproducible calculations and confidence/limitations.
4. **Orchestration**: Foundry-powered evidence selection and audience-aware narration; deterministic validation of all numeric assertions, event references and structured output. Optional LLM critic only for ambiguous cases; never invent football facts.
5. **Delivery**: timestamped, machine-readable overlay messages, server push/websocket to React/TypeScript client, modes for casual/analyst/club/player. Planned multilingual output and recap based on verified timeline.
6. **Infrastructure**: local replay and unit tests first, consumption-based Azure Foundry inference, Azure Container Apps only if economically justified; GitHub Actions, no long-lived cloud secrets.

## Key contracts
- `EventSource -> CanonicalEvent`
- `CanonicalEvent -> MatchState`
- `MatchState -> InsightCandidate(evidence_event_ids, measurements, window)`
- `InsightCandidate -> VerifiedInsight`
- `VerifiedInsight + AudienceProfile -> Narrative + OverlayPayload`

All provider parsing, model/SDK calls, and rendering must be isolated behind ports. Domain code must not import Foundry or StatsBomb libraries.

## Performance and evidence
- Deterministic replay fixed seed; recorded expected event-to-insight outputs.
- Detect and render the high press → turnover → dangerous pass → shot scenario.
- Measure ingest-to-insight and insight-to-overlay latency in demo environment; set targets only after baseline profiling.
- Track source IDs and metric calculation for every displayed factual claim; reject unsupported narrative claims.

## Scope guardrails
- No live Premier League feed or footage.
- StatsBomb open-data is a **reference**, not bundled training or redistributed event data; validate applicable license and attribution before reuse.
- No dependency on Wyscout or socceraction/Kloppy in MVP.
- No custom plugin framework; only minimal typed ports and adapters.
- No dedicated GPUs, AKS, or unlimited agent loops.
- No provisioning/billable Azure changes without explicit approval; free-trial spending limit must remain On.

## Open decisions for review
- Agent structure: orchestrated roles within one flow versus separate persistent agents; judge by latency, cost, observability, and actual collaboration.
- Which model and Foundry consumption SKU; inspect price/quota before deployment.
- Match simulation breadth versus polished representative scenarios.
- Scope of club/player mode, additional language(s), and full-time recap.
- GitHub Project #6 board mapping: connector supports repository issues but board membership is not currently available.

## Acceptance
End-to-end synthetic event replay, deterministic and evidence-traceable insights, agent-driven audience narratives, broadcast-style timed overlays, automated tests, cloud integration, useful demo, honest limitations.
