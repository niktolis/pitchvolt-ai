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

## Narrative SSE audit metadata

The ordinary narrative SSE update now carries optional `verification` and `trace` fields while preserving its existing headline, text, source, audience and evidence IDs. A successful server-owned narrative is `controlled`; a rejected or unavailable provider returns `deterministic_fallback`. Each trace step exposes only the orchestration role, action, elapsed milliseconds and an optional evidence-event ID. Prompts, raw model responses, credentials and exception messages are never serialized into SSE updates.

This is provenance for **publication decisions**, not semantic certification of unrestricted model-authored prose and not proof of paid Foundry inference. Foundry preview remains separately gated. No model deployment or Azure invocation is required for the offline regression tests.

## Offline shadow assessment of free-text Storyteller candidates

`matchpulse.shadow_validation.assess_candidate` evaluates proposed `NarrativeCandidate` responses **without publishing them**. An invalid evidence/claim manifest returns `invalid_claims`; a valid manifest returns `unverified_prose`, not a success state. The result schema enforces `publishable=false` and records only non-sensitive insight ID and claim/evidence counts, not model-produced wording or exception messages.

This distinction matters: a model can attach valid tactical claims to a sentence that fabricates goals, possession or player actions. Machine-readable claim verification alone cannot establish sentence-level entailment. The existing `verify_narrative` rejection and public narrative renderer stay unchanged. This module enables offline negative-control evaluation for a future, independently reviewed semantic verification strategy; it is not a replacement for one. No SDK calls, inference permission or Azure cost are added.

## Reproducible offline shadow benchmark

Run `uv run --frozen python -m matchpulse.narrative_eval` to print a deterministic JSON report. The scenario corpus is original synthetic football evidence, with valid structured facts, an invalid metric, mismatched evidence, and **plausible structured facts accompanied by fabricated goal/possession text**. Report fields include counts by verdict and an explicit `semantic_verification: not_implemented` marker. All candidates remain `publishable=false`.

This benchmark tests **claim validation and fail-closed publication policy**, not semantic entailment, model quality, inference latency, or hallucination detection within the raw text. It is deliberately no-cost and does not use Foundry. A future real-model benchmark should measure sampled candidate outputs and manual annotations separately, without treating this four-case synthetic fixture as an accuracy estimate.

## Next locally authorized live evaluation: observable decisions and shadow prose

After explicit PR review and merge, one operator-approved invocation of `python -m matchpulse.foundry_smoke` will request the existing two model roles only. The Analyst returns a structured plan and all canonical evidence must be retrieved through the read-only tool. Storyteller returns a structured selection and, optionally, `authored_headline` and `authored_text` as **untrusted, shadow-only proposals**. The backend continues to publish the prior deterministic verified narrative, ignoring these model-authored fields. The shadow evaluator classifies the proposal as unverified and never grants publication.

The local smoke report now includes allowlisted role decisions, per-role elapsed durations and token counts when obtainable from supported SDK response envelopes, plus an optional shadow assessment. Use `--show-unverified-prose` to display the proposal locally for human evaluation; by default its content is omitted. Shadow proposals are never sent on public SSE endpoints. Model usage may remain null depending on SDK behavior; treat null as unknown, never zero usage or zero cost. Operator must check Azure billing separately. The invocation remains no-retry with the existing two-role call budget and requires `--execute --acknowledge-billable-inference`; flags do not create a hard monetary cap.

Acceptance after merge: one locally approved run returns exactly two invocations, six evidence tool IDs, the controlled verified narrative, sanitized Analyst/Storyteller decisions, an unpublishable shadow assessment if both optional authored fields are returned, and clear usage availability status. An absent candidate or absent usage must be reported as incomplete evidence, **not** presented as successfully validated. The existing acceptance does not prove prose semantic entailment or production readiness.

Each subsequent product milestone follows one substantial PR → green checks → owner review/merge → independently authorized local live experiment. No inference authorization is implied by merging code.

## Schema failure diagnosis after the second live smoke

The second, explicitly approved live attempt failed in the Analyst SDK path with `ChatClientException` caused by a Pydantic `ValidationError`; it did not confirm a Storyteller invocation or model-authored shadow candidate. The error alone cannot identify a specific invalid field, whether the SDK validated the provider envelope or the generated structured response, or whether tokens were billed. Do not infer those facts from the exception class.

The smoke failure report now records the last attempted role, number of attempted role invocations, completed roles, and only allowlisted Pydantic error type codes plus the number of location segments (not field paths, input values, exception messages or raw responses). An unrecognized SDK validation layout will still produce an empty diagnostic list. This is diagnostic-only; it does not relax schemas, bypass verification, retry, or authorize additional Azure inference. Offline tests verify the diagnostic redaction contract. Any further live test requires separate operator approval and a reviewed PR.

## Grounded authored-prose eligibility experiment (local only)

The first truly AI-authored Storyteller sample contained unsupported qualitative assertions ("superior", "sustained", "controlling opposition play"), despite correctly matching the four typed claims. General semantic entailment cannot be established with a string filter or verified claim manifest. The new `grounded_prose` module therefore supports a deliberately **finite, reviewed grammar** containing exactly two evidence-derived sentence variants. It does not claim to verify arbitrary language or novel tactical interpretations.

The Storyteller is supplied the two complete allowed headline/text pairs and asked to choose one exactly. Offline `assess_grounded_prose` first verifies the canonical typed claims and exact event IDs, then matches the headline and full paragraph byte-for-byte against an approved pair generated from deterministic metrics. Added clauses, unsupported interpretations, altered numeric values, hallucinated scores/players, and any other unrecognized wording fail closed. Only matching pairs are *eligible for a future publishing policy*; no public SSE publishing change has been made. In the local smoke output `bounded_grounding.eligible` and `matched_grammar` distinguish this narrow lexical eligibility from the existing shadow status (which remains non-publishable).

Tradeoff: these two variants are largely backend-controlled phrasing selected by a real model, not unconstrained creative prose. This is a deliberately narrow first step toward safe publication, **not the eventual goal of independently verifiable original broadcast commentary**. Broader semantic evaluation requires decomposed evidence-linked assertion spans and independently validated entailment. No remote verifier/third inference call is enabled.

Next local live-test acceptance after PR review/merge and fresh cost approval: two successful roles and six model evidence retrievals; original typed role decisions; `bounded_grounding` with explicit eligibility (pass or reject), untrusted generated text, deterministic published narrative, measured per-role durations and honest token availability. A grammar miss is a meaningful safety rejection, not proof of semantic safety for arbitrary prose. Intermittent SDK schema failures and absent token telemetry remain risks.

## Explicit specialist initialization policies

Versioned agent initialization instructions are defined in `src/matchpulse/agent_policies.py` (`grounded-v1`). The Analyst's stable policy requires exhaustive read-only evidence inspection, exact IDs and no invented player or outcome facts. The Storyteller's stable policy defines audience-aware output, prohibits unsupported tactical superlatives and requires verbatim selection from the two reviewed headline/text variants for the local safety experiment. An Editorial policy is defined but Editorial inference is not invoked. Actual match evidence, approved options and output schemas are supplied **per request**; there are no long-running agents, persistent model memory or hidden coaching requests. Policy tests run entirely offline. Prompt discipline improves reliability but does not provide semantic proof of arbitrary prose; the bounded grammar gate and deterministic public renderer remain authoritative.
