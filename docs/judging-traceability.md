# Judging Traceability Matrix

Status: implementation evidence reviewed 18 October 2026. Updated after replay, team/roster, temporal and offline Foundry preparation changes. The five judging criteria are treated as equal priorities; final submission wording must still be checked against the official rules immediately before hand-in.

| Criterion | Current evidence | Remaining proof before submission | Tracking |
|---|---|---|---|
| Technological Implementation | Versioned Pydantic event model, deterministic stream invariants/detectors, fixed synthetic scenarios, FastAPI/SSE replay/evidence API, generated TS contracts, Python/frontend/D2 CI, containerized runtime | Measured performance and final deployed proof | #1 #2 #3 #6 |
| Agentic Design & Innovation | Accepted selective Analyst + Storyteller + deterministic verifier architecture; evidence endpoint already forms the read-only factual tool boundary | Implement actual Microsoft Foundry orchestration, tool-call/handoff trace, unsupported-claim rejection, latency/cost comparison | #4 |
| Real-World Impact & Applicability | Replay cursor, reconnect semantics, evidence inspection, single deployable OCI workload, documented scaling limitations and cost guardrails | Production telemetry, fault/timeout demonstration, accessible endpoint and cost summary | #5 #6 #8 |
| User Experience & Presentation | Live React pitch, synchronized event timeline, tactical insight card, evidence drill-down, replay controls and casual/analyst/club presentation modes | Visual polish review, judge walkthrough capture, AI narrative arrival in the same interface | #5 #8 |
| Challenge Adherence | Synthetic-data provenance; implemented Ingest → Interpret → Render and deterministic personalization preview; Explain boundary prepared through evidence contracts | Foundry Explain step, verified personalized narratives, final end-to-end wow sequence; recap/multilingual only if core demo is secure | #2 #3 #4 #5 #7 |

## Demo spine

1. Replay fictional teams and players through pressure → failed pressured pass → turnover → carry/pass → shot.
2. Show the canonical event moving on the pitch and the ordered timeline.
3. Let the detector publish a high-press insight immediately after the shot.
4. Open the insight's exact evidence records and metrics.
5. Switch casual/analyst/club modes while the underlying facts remain unchanged.
6. Once Foundry is implemented, show the slower grounded narrative update for the same stable insight ID and expose the agent/evidence trace.

## Quality gates

- **G0 planning — complete:** reviewed architecture, rubric mapping, backlog and financial guardrails.
- **G1 deterministic data/core — substantially complete:** canonical schema, synthetic scenarios, invariants, replay and detector tests.
- **G2 intelligence/agentic — partial:** deterministic intelligence complete for the implemented scenarios; Foundry offline adapter/tool orchestration and bounded verifier exist, but complete successful real two-role acceptance and a production model path remain unproven.
- **G3 UX — first vertical slice implemented:** live broadcast, replay, evidence and deterministic audience modes; AI narrative integration remains.
- **G4 submission — not started:** Azure site deployed; measured latency/cost, demo recording, final README/rules/license/secrets checks remain.

## Submission constraints

- Synthetic fictional data only unless a future source is explicitly authorized and licensed.
- Private development may require a reviewed public-source publication before hand-in; perform a secrets/license scan first.
- Azure Free Trial spending limit must remain enabled.
- Budget alerts are observability, not a hard kill switch.
- No Azure provisioning or billable-resource modification without explicit project-owner approval.
- Reserve sufficient approved trial capacity for the judging window rather than consuming credits during development.

## Provider-compatibility evidence (issue #15)

The originally synthetic `statsbomb_high_press` scenario exercises StatsBomb-shaped JSON with its provider coordinate system, nested event families and validated explicit recovery semantics. It reaches the unchanged processor, SSE and UI. Native/adapted deterministic kind and metrics are checked in tests. This **does not** claim integration with historical StatsBomb Open Data or authorized redistribution of real match records.

## Milestone A / B Foundry evidence boundary (PR #130)

An offline full-roles integration test uses mock SDK agents to retrieve
the same six canonical evidence events, execute Analyst → Storyteller →
verifier, prove strict composition rejection and deterministic fallback,
and prevent creative AI prose publication. A no-cloud local preflight
checks pinned optional SDK dependencies, endpoint shape and one-time smoke
settings, including zero automatic HTTP retries. This is **not** live
Foundry inference, a completed agentic demonstration or a measured Azure
cost; judge-facing claims must wait for the user's single separately
authorized local run and sanitized evidence.
