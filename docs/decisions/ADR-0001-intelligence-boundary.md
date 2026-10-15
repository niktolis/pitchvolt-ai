# ADR-0001: Deterministic match intelligence with agent-orchestrated explanations

**Status:** Accepted. Deterministic intelligence boundary implemented; Foundry explanation path pending.

## Context

The challenge values explainable, real-time football intelligence and compelling agentic AI, with synthetic data and audience personalization. Purely LLM-generated football metrics are non-reproducible and difficult to verify.

## Decision

A deterministic domain core owns state, metrics, tactical triggers, provenance and evidence. Foundry-based orchestration consumes verified insights and produces audience-specific narratives plus render instructions. Numeric claims and event references must be verified against evidence; publication fails closed or falls back to deterministic templates when verification is unavailable.

## Implemented evidence

- `MatchEvent` and stream invariants are provider-neutral, versioned Pydantic contracts.
- `MatchProcessor` owns possession transitions, tactical classification and metrics.
- FastAPI publishes existing domain outputs rather than reimplementing tactical logic.
- Evidence retrieval returns the canonical events referenced by the insight.
- React audience modes consume one factual insight payload and change presentation only.
- No model API is called on the deterministic fast path.

The Microsoft Foundry Analyst/Storyteller workflow and deterministic narrative-claim verifier remain pending.

## Consequences

- Positive: reproducible tests; inspectable evidence; lower token cost and latency; portable input providers; clear studio integration contract.
- Negative: detectors require explicit domain modeling; constrained agent scope risks seeming less novel unless tool use, decisions and verification are shown transparently.
- Mitigation: purposeful specialist-agent workflow with auditable evidence calls and handoffs rather than unbounded LLM invocations per event.

## Alternatives not chosen

- LLM as the source of football statistics: fabricated-fact, latency and reproducibility risk.
- Full microservices/multi-agent distributed system for MVP: excessive deadline, operational and cost risk.
- Provider-specific analytics coupled to an external football schema: inhibits provider replacement and violates the synthetic-data-first boundary.

## Follow-up

Implement ADR-0002's selective Analyst + Storyteller orchestration behind a port, add deterministic narrative claim verification, measure latency/cost/quality, and record the selected Foundry model/SKU only after explicit cost approval.
