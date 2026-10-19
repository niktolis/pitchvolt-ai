# Foundry runtime guardrails — issue #4

Microsoft Agent Framework with Foundry project inference remains the approved integration direction. Official references:
- https://learn.microsoft.com/en-us/agent-framework/agents/providers/microsoft-foundry
- https://learn.microsoft.com/en-us/agent-framework/agents/structured-outputs

As of 16 October 2026, `agent-framework-foundry` 1.15.0 was published 15 October 2026, but **the initial foundation PR did not install or upgrade the SDK**. Before enabling it, the exact optional dependency graph must be locked and validated against the target model's structured-output support. The existing `FoundryRoles` adapter continues to accept Pydantic structured outputs; the inference switch defaults to disabled and refuses client/credential initialization without explicit approval.

## Local static guardrails added
- Project endpoint must be HTTPS, under `*.services.ai.azure.com`, without embedded user credentials, query strings or URL fragments.
- Deployment name must be supplied explicitly; no implicit discovery or automatic provisioning.
- Hard local per-role output cap: default 256 tokens; absolute supported maximum 1024 tokens.
- Two-role narrative inference budget fixed at two model invocations (Analyst and Storyteller). Additional Editorial calls are not silently enabled; any future policy requires separately budgeted approval.
- No model calls or credential discovery are performed by tests or this feature branch.

These controls are **application-level request limits, not a guaranteed Azure spending stop**. They do not cap aggregate traffic, input tokens, SDK retries or cloud billing. A production cost review must also limit rate/concurrency, input sizes, max requests/session, retries, and total scheduled deployment duration; review actual Azure subscription spending limits separately.

## Remaining integration work
1. Lock/test `agent-framework-foundry` and `azure-identity` as optional packages with a version-compatible dependency graph, without changing the default deployment image until approved.
2. Replace local SSE narrative role implementations with configurable Foundry roles only in explicitly approved inference mode; retain deterministic fallback for unavailable providers.
3. Validate the model's structured output support, policy-compliant trace capture, real tool handoffs and token usage; compare against a single-agent baseline.
4. Confirm one-time Foundry User RBAC for the existing GitHub OIDC service principal, and preserve the free-trial spending limit. The post-merge one-fixture CI smoke has standing owner authorization; new deployments or an expanded inference workload still require explicit approval.

## Current runtime policy (supersedes original planning constraints)

Foundry SDK dependencies are installed and pinned for isolated tests. One full Azure-authenticated Analyst → Storyteller → Verifier run passed on 18 October 2026. After PR merge, `.github/workflows/foundry-merge-smoke.yml` automatically tests one synthetic insight without user interaction. No billable calls run on ordinary commits, PR updates, or unmerged closures. The workflow uses OIDC, exact merged commit checkout, an allowlisted report, no retries, and a nonzero failure status. Production continues locally controlled narrative output.
