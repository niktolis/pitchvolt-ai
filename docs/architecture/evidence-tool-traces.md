# Read-only evidence tools and trace — issue #4

Each narrative request loads a validated immutable `EvidenceBundle` and explicitly looks up each cited event through the `EvidenceTool.get_event(insight_id, event_id)` method. The in-memory tool refuses events outside that insight's evidence manifest; cross-match and mismatched event identities fail closed. The orchestrator records ordered `TraceStep` records for bundle lookup, each individual cited event lookup (with event ID and execution duration), Analyst plan, Storyteller selection and publication verifier or rejection. Invalid/missing evidence produces a deterministic fallback, not unverified generated content.

**Transparency:** these are application-managed, offline read-only tool calls. They are *not* LLM-selected tools or proof of Azure Foundry tool-calling capability. They are an auditable boundary to expose to actual Foundry agents in the later inference-approved milestone. Trace duration values describe local steps only, not cloud inference latency.

## Hackathon activation and demo gates
1. **Offline dry run:** deterministic high-press and counterattack replay; show insight evidence IDs and ordered evidence/agent/verifier trace steps. Demonstrate fabricated-reference rejection and safe fallback.
2. **Foundry connectivity smoke test (future, explicit authorization):** review exact project endpoint, model deployment, expected request/input/output token consumption, retry/concurrency budgets, and trial spending controls. Confirm SDK structured-output compatibility with one bounded approved invocation, then record provenance and usage.
3. **Judge-ready demo:** compare identical canonical insight between local narrative and Foundry selection, stream asynchronous arrival with unchanged event SSE, expose verifiable evidence, capture useful screen recording and reproducible setup. Keep fallback path available if external service fails.
4. **Acceptance evidence:** capture sanitized traces, correctness metrics, per-request tokens/cost and p50/p95 latency (only after approved inference), update `docs/judging-traceability.md`. Never claim local traces are model traces.

No model is deployed or contacted by this change. The provider gate remains disabled.
