# ADR-0002: Selective specialist-agent orchestration (proposal)

**Status:** Proposed — user requested tradeoff discussion before approval.  
**Context:** Hackathon Agentic Design & Innovation is 20% of judging criteria; deadline October 27, 2026, Azure Free Trial only.

## Options
1. Single model with role prompts: least complexity but weak evidence of distinct agent collaboration.
2. Three independently deployed autonomous agents: strong theoretical demonstration; multiplies operational, latency and expense risk.
3. **Recommended: one orchestrated, selectively invoked specialist-agent workflow**, using Microsoft Agent Framework where supported by the selected Foundry model/service.

## Proposed roles
- **Analyst**: consults read-only, typed match evidence tools; selects and contextualizes verified tactical insight candidates. Cannot generate source events or overwrite deterministic metrics.
- **Storyteller**: renders the same evidence into typed audience-specific narratives, languages and synchronized overlay content.
- **Editorial reviewer**: optionally adjudicates complex or contested interpretations; a deterministic claim validator always verifies IDs, numeric assertions, schema and event provenance. The LLM reviewer never replaces the deterministic gate.
- **Orchestrator**: schedules work based on insight importance, budget, latency and confidence; records handoffs, calls, rejection reasons and safe fallback to templates.

## DRY / single source of truth
- One canonical schema for event, evidence, audience profile, and published narrative.
- Shared protocol for evidence tools; single immutable factual source for all view modes.
- Shared prompts for common grounding constraints; role-specific instructions contain only their delta.
- Shared orchestration interface for both Foundry and local test doubles.
- Shared serialization validators between API and UI via generated schema, not hand-copied types.
- No speculative reusable framework or abstraction without a second real use case.

## Staged adoption
1. End-to-end deterministic core and single grounded narrative, with telemetry.
2. Introduce distinct Analyst + Storyteller workflows and show tool calls and agent handoff.
3. Add optional Editorial reviewer only if measurable improvement to grounding/quality within budget and latency.
4. Demonstrate actual multi-agent traces and rejected unsupported claim; compare cost/latency/quality against single-agent baseline.

## Acceptance/evaluation
- Cross-mode factual consistency and evidence ID traceability.
- Repeatable tool-call traces that show meaningful agent collaboration.
- Budget per scenario and measured p50/p95 latency under actual model deployment.
- Clear automated tests for fallback and invalid claims.
- Record cost/quality/time comparison of orchestrated approach versus one agent.

## Explicit non-goals
- Three always-on hosted agents, open-ended conversations, LLM for deterministic stats, Foundry visual workflows scheduled for retirement Dec 1 2026.

## Approval gate
Do not treat this ADR as accepted until project owner approves the selective multi-agent design and escalation criteria.
