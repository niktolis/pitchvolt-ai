# Foundry live-readiness request controls (issue #4)

Offline safeguards added ahead of deployment: at most one Analyst and one Storyteller `Agent.run` invocation per `FoundryRoles` instance, including failed/timeout attempts. Editorial cannot run. The request prompt has a configurable character cap (default 12,000, range 256–16,000); each role has a six-second timeout (configurable 0.1–30 seconds); Analyst evidence lookup has a default 12-call cap (max 32). Existing per-role output caps and evidence manifest checks remain.

**Limits are per adapter instance, not per web user or service lifetime.** Agent Framework may execute multiple internal model requests or retries within one `Agent.run`; these guards do **not** enforce a hard aggregate API-request, monetary or input-token ceiling. The tool callable refuses excess operations, but SDK-side tool-loop behavior is not verified. A caller cancellation/timeout does not guarantee Azure stops charging for an already dispatched request. These constraints are prerequisites, not production-grade spending enforcement.

No **production** inference is enabled. The bounded automatic CI smoke is authorized after a reviewed PR merges into `main`. Existing pair: Analyst GPT-5 mini Global Standard; Storyteller GPT-4o Standard in Sweden Central. Before live testing review exact project endpoint, role-based Azure authorization, version-specific SDK tool registration, structured outputs, response options, token accounting and retry semantics. New deployments still require explicit owner approval. The existing bounded merge-only live smoke is covered by standing authorization; use synthetic fixtures, no arbitrary user input.

The isolated local smoke has been hardened to `http_max_retries=0`
(with no role-level retries). This reduces accidental duplicate billing
but cannot bound tool-call/model-request rounds or guarantee a monetary
ceiling. Optional installed packages and the Foundry project URL can now
be validated without authentication via `pitchvolt.foundry_preflight`.
Public provider remains local/deterministic.

Existing deployments verified 18 October 2026: `matchpulse-gpt5-mini` (GPT-5 mini Global Standard) and `matchpulse-gpt4o` (GPT-4o Standard) in Sweden Central, both Succeeded/20,000 TPM. The smoke-only budget is 6144/1024 output tokens and 30 seconds per role; this does not authorize public inference or guarantee any monetary limit.

**Verified 18 October:** One local real two-role smoke passed (6/6 evidence, both structured decisions, controlled deterministic publication), Analyst ~14.93s, Storyteller ~3.84s, token usage null/unknown. The 19 October operating policy runs future equivalent tests only on GitHub Actions `pull_request_target:closed` merged into `main`; no PC smoke or per-merge consent. Production remains local/deterministic.
