# Narrative foundation (issue #4)

This PR introduces typed evidence and claim contracts before adding a billable model adapter. The canonical match processor remains authoritative. `EvidenceBundle` requires exact ordered source IDs and accepted synthetic provenance. `verify_claims` checks typed insight/team/metric/event references against deterministic evidence. A correct set of references **does not prove arbitrary prose is true**: `verify_narrative` therefore fails closed until a semantic publication policy is approved. A separately labeled deterministic fallback can render only canonical facts for casual, analyst and club audiences.

This is **not** a Foundry integration, completed agent choreography, or verified AI-generated narrative. Issue #4 remains open. Microsoft model calls and Azure changes are prohibited without explicit prior approval and cost review.

## Required decisions before wiring the agents

1. Whether model output is restricted to typed claims plus controlled server-rendered text, or arbitrary prose is allowed subject to a defined semantic verifier and escalation policy.
2. Which Foundry execution API/model deployment will be used (currently no deployment has been approved). Confirm the credential and model lifecycle under the zero-out-of-pocket Azure Free Trial guardrail before enabling any real inference.

Implementation staging: contract/claim checks -> Analyst evidence tool protocol -> Storyteller controlled output -> asynchronous narrative SSE update -> recorded tool/handoff traces and latency/cost comparison -> optional Editorial gating.
