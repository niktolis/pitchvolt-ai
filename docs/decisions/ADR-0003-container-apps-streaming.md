# ADR-0003: Container-native Azure Container Apps with two-speed live intelligence

**Status:** Accepted in principle by project owner on 2026-10-15. Operational choices are subject to profiling and cost review.

## Decision
Package backend and UI as OCI containers (one backend deployment and, if needed, one frontend deployment initially). Target Azure Container Apps **Consumption**, not AKS, for the hackathon. Keep Docker-compatible local development and parameterized Bicep deployment; no environment provisioning until approved with cost estimate.

**Real-time does not mean one LLM invocation per football event.** Use two distinct execution paths sharing canonical event/state and evidence contracts:

1. **Fast path**: synthetic stream → source adapter → validated canonical events → deterministic state/metrics/detectors → machine-readable overlay events → WebSocket/SSE clients. Operates without Foundry availability.
2. **Narrative path**: detector emits high-value insight candidates → bounded queue / coalescing and rate-limited orchestration → Analyst and Storyteller using read-only evidence tools → always-on deterministic verification → optional Editorial review → asynchronous narrative update for same stable insight ID. Stale outputs are dropped. Graceful fallback to evidence-backed templates.

## Constraints and tradeoffs
- Keep state and stream ingestion independent of a container replica's lifetime. A single replica may hold state only for the hackathon MVP; document the scaling limitation and use one replica while demonstrating. For multi-replica, introduce an external event log/state store with ordering and idempotency before scaling.
- Event delivery sequence IDs, replay cursor, idempotent consumption, bounded queues, and disconnect recovery must be tested.
- WebSockets suit interactive live overlays but sustained connections may keep Container Apps replicas active; SSE is a possible one-way alternative. Evaluate actual limits/usage.
- Prevent narrative model calls from blocking ingestion or overlays. Prefer short timeouts, capped requests, and prioritization/late-response discard.
- Scaling to zero saves idle cost but causes cold starts; deliberate min replica decision required before demo. No AKS deployment for the MVP.
- DRY: canonical schema, single evidence store/validator, typed transport contracts, no duplicated tactical logic across generator, agent prompts, and UI.

## Provisional service-level objectives (not demonstrated)
- Fast path (ingest → deterministic overlay): target p95 < 500 ms under synthetic representative workload.
- Narrative path (insight trigger → AI overlay): target p95 < 5 s for ordinary insights, subject to Foundry model quota and measured latency.
- Report measured p50/p95, event throughput, agent calls, token spend, reconnect behavior, and dropped/stale narratives.
These are **targets**, not promised production performance.

## Azure credit controls
Subscription FreeTrial with spendingLimit On. Use consumption deployment with explicit replica, CPU/memory, concurrency, telemetry retention and model-token limits; record a cost estimate and seek user approval before provisioning. Avoid AKS clusters, managed GPU deployments and always-running background workers.

## Scope
Synthetic football event streaming for hackathon. No real Premier League feed, video ingest, or rights are implied. Provider adapters remain swappable via canonical schema. A future authorized external football feed can replace the generator without restructuring downstream stages.

## Verification gates
- Local replay streamed at simulated match time, including acceleration and deterministic golden insight sequence.
- UI sees immediate deterministic overlays before slower narratives.
- Service interruption or agent timeout does not stop state processing.
- Same evidence and facts across personalized audience modes.
- CPU/memory and model usage documented; deployment suitable for judging window.
