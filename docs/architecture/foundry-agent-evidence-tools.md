# Foundry Analyst evidence function tools — issue #4

The Analyst receives a request-scoped local Python callable in its Agent Framework run options: `get_evidence_event(event_id)`. Only event IDs in the current immutable, validated EvidenceBundle can be retrieved. The tool returns canonical event JSON, records references, rejects unknown IDs, and never mutates the match state.

The structured Analyst plan is rejected unless the tool has retrieved every cited event and the plan preserves the exact canonical evidence manifest. This fail-closed condition protects against a model guessing IDs without examining supporting events. The Storyteller remains constrained to typed decisions, and the deterministic verifier exclusively owns publishable facts.

**Honest validation boundary:** offline fake Agent tests invoke this callable as a simulated agent tool request. A model-initiated tool call with the installed SDK, structured-output compatibility, telemetry, and billing have **not** yet been demonstrated against Foundry. No Azure inference is enabled by these changes.

## Planned connectivity and hackathon demo
1. Review project endpoint, deployment, authentication approach, estimated tokens/cost, request concurrency, retry limits and Azure trial protections.
2. Obtain separate owner authorization for a tightly bounded real Foundry connectivity smoke test; capture structured output and actual tool-call observations.
3. Demonstrate fictional match replay, canonical insight, agent-requested evidence, grounded audience-specific narrative, trace, and deterministic fallback in the UI.
4. Measure model usage, latency and cost and record sanitized reproducible judging evidence.

The provider stays hard-disabled in production until separately approved.
