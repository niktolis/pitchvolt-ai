# Controlled Analyst / Storyteller workflow — issue #4

The project-owner approved controlled natural-language generation and the Microsoft Agent Framework + Foundry project inference direction. The default cloud runtime remains disabled until a reviewed model deployment, configuration, cost estimate and spend controls are explicitly approved.

The `matchpulse.workflow` module adds the actual deterministic local orchestration state machine: read-only evidence lookup → Analyst structured angle → Storyteller structured style → server-owned bounded narrative renderer → publish or deterministic fallback. Every narrative uses exact canonical metrics, team identity and insight/evidence IDs. The model never controls arbitrary prose or rendered quantities. Role-specific response schemas use Pydantic `extra="forbid"`. A fabricated ID, changed evidence manifest, requested-audience mismatch or angle mismatch fails closed.

The local `AnalystDouble`/`StorytellerDouble` used in tests are **test doubles**, not deployed or simulated Foundry agents. The workflow traces include read-only lookup, role decisions and verifier execution with durations, but these are local orchestration measurements, *not Azure token/cost or LLM latency measurements*. The `NarrativeCandidate` free-text validator continues to reject arbitrary prose.

## Microsoft integration target

Official Microsoft guidance documents `Agent(client=FoundryChatClient(project_endpoint=...,model=...,credential=...))` from `agent-framework-foundry`, using the project inference Responses API. We will keep the client provider behind an explicitly configured port, instantiate separate Analyst and Storyteller agents for each request, request their structured outputs, and feed their selections into the **existing** local publication gate. No hosted agent service, model deployment, separate service or SDK dependency is added by this non-billable foundation.

Source: https://learn.microsoft.com/en-us/agent-framework/agents/providers/microsoft-foundry

## Pending integration proof

- Bind actual Microsoft Agent Framework `Agent` invocations to the protocol with a pinned optional dependency and frozen lock, after reviewing model-specific structured-output compatibility.
- Implement selective async SSE narrative update (same insight ID), stale-response handling and UI receipt; fast events stay independent.
- Verify prompt-injection/unsupported narrative claim cases, timeout/error fallback, and role/tool trace samples.
- Compare orchestrated vs single-agent baseline using real model usage accounting, latency p50/p95 and output quality.
- Evaluate conditional Editorial role only on measured necessity.

No cloud execution or billable resources authorized in this PR.

## Verified fact composition (incremental issue #4 slice)

The Storyteller may optionally provide `fact_order`: a permutation of `team`, `tactic`, `transition`, and `actions`. The server checks that each canonical fact appears exactly once, maps the slots to validated insight values, and renders the text locally. Missing, duplicated, and unknown slots fail closed. Omitting `fact_order` retains the earlier audience-specific sentence templates for backward compatibility.

This permits model-selected **information ordering**, not free-form AI-authored prose or arbitrary tactical explanations. The existing `NarrativeCandidate` publication verifier intentionally continues to reject unbounded generated text. The optional Foundry provider remains behind the existing explicit inference-approval gate; tests use no Azure calls. Full model-authored natural-language generation would require an additional reviewed semantic-grounding and publication policy before enabling it. No production inference, model deployment or cost approval is implied by this slice.
