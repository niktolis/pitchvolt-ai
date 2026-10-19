# Judging Traceability Matrix

Status: implementation evidence reviewed 18 October 2026. Updated after replay, team/roster, temporal and offline Foundry preparation changes. The five judging criteria are treated as equal priorities; final submission wording must still be checked against the official rules immediately before hand-in.

| Criterion | Current evidence | Remaining proof before submission | Tracking |
|---|---|---|---|
| Technological Implementation | Versioned Pydantic event model, deterministic stream invariants/detectors, fixed synthetic scenarios, FastAPI/SSE replay/evidence API, generated TS contracts, Python/frontend/D2 CI, containerized runtime | Measured performance and final deployed proof | #1 #2 #3 #6 |
| Agentic Design & Innovation | Live Azure Foundry Analyst and Storyteller produced typed decisions with 6/6 evidence tool calls; deterministic verifier published controlled facts for one synthetic insight | Merge-only CI automation, accurate cost telemetry, independent semantic evaluation of unbounded model prose | #4 |
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
- **G2 intelligence/agentic — verified isolated slice:** deterministic intelligence plus the real Analyst → Storyteller → verifier smoke passed on one synthetic high-press insight; merge-only CI regression is implemented, while SDK token accounting, generality and production inference remain separate issues.
- **G3 UX — first vertical slice implemented:** live broadcast, replay, evidence and deterministic audience modes; AI narrative integration remains.
- **G4 submission — not started:** Azure site deployed; measured latency/cost, demo recording, final README/rules/license/secrets checks remain.

## Submission constraints

- Synthetic fictional data only unless a future source is explicitly authorized and licensed.
- Private development may require a reviewed public-source publication before hand-in; perform a secrets/license scan first.
- Azure Free Trial spending limit must remain enabled.
- Budget alerts are observability, not a hard kill switch.
- No Azure provisioning or billable-resource modification without explicit project-owner approval. The bounded existing-deployment smoke is pre-authorized once per reviewed PR merge to main.
- Reserve sufficient approved trial capacity for the judging window rather than consuming credits during development.

## Provider-compatibility evidence (issue #15)

The originally synthetic `statsbomb_high_press` scenario exercises StatsBomb-shaped JSON with its provider coordinate system, nested event families and validated explicit recovery semantics. It reaches the unchanged processor, SSE and UI. Native/adapted deterministic kind and metrics are checked in tests. This **does not** claim integration with historical StatsBomb Open Data or authorized redistribution of real match records.

## Microsoft Foundry live evidence and automatic regression — 19 October 2026

**Verified on 18 October against the real Azure project (one synthetic
fixture):** existing GPT-5 mini Analyst inspected all six event IDs through
read-only tools and returned a structured AnalystPlan (transition angle);
GPT-4o Storyteller returned a structured selection with the full
`[team,tactic,transition,actions]` ordering; deterministic verifier published
controlled source-backed narrative (`source=controlled`). Timings:
Analyst 14.93 seconds, Storyteller 3.84 seconds, CLI exit 0.
Original generated prose remained shadow-only and outside bounded grammar.
Model token telemetry was unavailable/null, **not zero billed**.

One merger-triggered Azure OIDC workflow now provides ongoing regression
against the same deterministic fixture. It runs only after a reviewed
PR is merged into `main`, not on pushes or PR commits; no per-run
operator sign-off or Mac command is required. It publishes allowlisted
GitHub job summary and JSON artifacts with observed model roles, event IDs,
verifier outcome, latency, optional usage and status. A first-run OIDC/RBAC
failure is possible until the existing CI principal is granted Foundry User
on the project; automation design and one known-good user execution should
not be confused with a completed successful CI run.

Scope remains deliberately narrow: this is **not** a claim that generated
free-form broadcaster commentary is semantically entailed by evidence, that
production UI is backed by Foundry, or that trial credits are unlimited.
Production provider stays local; the free trial spending limit must remain
enabled. Manual approval still applies to every merge and new cloud
resources/expanded model workloads, **not** to each bounded post-merge smoke.

## First authenticated merge-only Foundry test — PR #135, 19 October

[Cloud workflow run 39211398821](https://github.com/niktolis/pitchvolt-ai/actions/runs/39211398821)
authenticated with the correct immutable PR subject and
completed both real model roles, 6/6 source evidence events, full typed
decision contracts and controlled verifier publication. Analyst 11.57s,
Storyteller 3.08s. Overall exit **FAIL** because an optional generated
shadow candidate was absent; the subsequent acceptance fix retains
strict evidence/verifier checks without mandating exploratory prose.
No unverified model prose was published. Token usage remains unknown.
