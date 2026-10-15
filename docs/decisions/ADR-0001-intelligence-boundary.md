# ADR-0001: Deterministic match intelligence with agent-orchestrated explanations

**Status:** Accepted in principle by project owner, implementation pending.

## Context
The challenge values explainable, real-time football intelligence and compelling agentic AI, with synthetic data and audience personalization. Purely LLM-generated football metrics are non-reproducible and difficult to verify.

## Decision
A deterministic domain core owns state, metrics, tactical triggers, provenance and evidence. Foundry-based orchestration consumes verified insights and produces audience-specific narratives plus render instructions. Verify numeric claims and event references against the evidence; fail closed or fall back to deterministic templates when unavailable.

## Consequences
- Positive: reproducible tests; inspectable evidence; lower token cost and latency; portable input providers; clear studio integration contract.
- Negative: detectors require domain modeling; constrained agent scope risks seeming less novel unless tool use, decisions and verification are shown transparently.
- Mitigation: purposeful agent workflow with explicit specialist tasks and auditable traces rather than three unbounded LLM invocations per event.

## Alternatives not chosen
- LLM as the source of football statistics: risk of fabricated facts, latency and unreproducible metrics.
- Full microservices/multi-agent distributed system for MVP: too expensive and complex for deadline.
- Tightly coupling StatsBomb JSON to internal analytics: inhibits dataset/provider replacement.

## Follow-up
Record explicit ADRs for selected model/SKU, streaming transport, and initial scenario coverage when evidence is available.
