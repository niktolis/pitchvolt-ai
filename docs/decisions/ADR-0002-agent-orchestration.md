# ADR-0002: Selective specialist-agent orchestration (proposal)

**Status:** Accepted — approved by project owner on 2026-10-15.  
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

## Approval and execution policy
Approved by project owner on 2026-10-15: selective specialist-agent orchestration. Analyst and Storyteller handle substantive narrative workflows; deterministic verification always runs; Editorial review is conditional on uncertainty, failed factual checks, or high-impact interpretation. Use measured cost, latency, and output quality to tune escalation thresholds. Changes to this architectural policy require a new review.

## Addendum — heterogeneous model assignment (approved 17 October 2026)

The project owner approved **different inference models per specialist role**. The selection is configuration, not a claim of live model validation:

| Specialist | Intended Foundry deployment | Responsibility | State |
|---|---|---|---|
| Analyst | GPT-5 mini, Global Standard | Model-requested, read-only evidence tools; select grounded tactical angle and preserve source IDs | Adapter/tool boundary implemented; live execution pending |
| Storyteller | GPT-4o mini, Regional Standard | Select audience-sensitive framing from the verified Analyst plan; templates render final prose | Adapter implemented; live execution pending |
| Editorial reviewer | **Unassigned**, conditional | Review high-uncertainty interpretations only if measured quality benefit justifies extra cost/latency | Not implemented; do not imply three active agents |

The **Orchestrator** is deterministic coordination code, not a fourth LLM agent. The **Verifier** is a deterministic publication gate, not a model or fifth agent. An Editorial review never overrides verification.

Each specialist must receive an independently configurable deployment/client, model-specific request settings, output-token cap, timeout and usage/cost telemetry. Do not reuse one implicit model or blindly share GPT-5 reasoning parameters with GPT-4o. Compare heterogeneous performance against a same-model baseline on exactly the same canonical fixture/evidence; record token usage, grounding accuracy, p50/p95 latency and observed cost before asserting improvement.

Neither deployment is currently proven available and no inference is approved by this addendum. Live inference requires separately reviewed project endpoint, subscription quota, per-model deployment/cost safeguards and explicit owner approval.

[Role assignment diagram](../architecture/diagrams/agent-orchestration.d2) · [Architecture entry point](../architecture/README.md).
