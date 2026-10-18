# Controlled Analyst / Storyteller workflow — issue #4

The project-owner approved controlled natural-language generation and the Microsoft Agent Framework + Foundry project inference direction. The default cloud runtime remains disabled until a reviewed model deployment, configuration, cost estimate and spend controls are explicitly approved.

The `pitchvolt.workflow` module adds the actual deterministic local orchestration state machine: read-only evidence lookup → Analyst structured angle → Storyteller structured style → server-owned bounded narrative renderer → publish or deterministic fallback. Every narrative uses exact canonical metrics, team identity and insight/evidence IDs. The model never controls arbitrary prose or rendered quantities. Role-specific response schemas use Pydantic `extra="forbid"`. A fabricated ID, changed evidence manifest, requested-audience mismatch or angle mismatch fails closed.

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

`pitchvolt.shadow_validation.assess_candidate` evaluates proposed `NarrativeCandidate` responses **without publishing them**. An invalid evidence/claim manifest returns `invalid_claims`; a valid manifest returns `unverified_prose`, not a success state. The result schema enforces `publishable=false` and records only non-sensitive insight ID and claim/evidence counts, not model-produced wording or exception messages.

This distinction matters: a model can attach valid tactical claims to a sentence that fabricates goals, possession or player actions. Machine-readable claim verification alone cannot establish sentence-level entailment. The existing `verify_narrative` rejection and public narrative renderer stay unchanged. This module enables offline negative-control evaluation for a future, independently reviewed semantic verification strategy; it is not a replacement for one. No SDK calls, inference permission or Azure cost are added.

## Reproducible offline shadow benchmark

Run `uv run --frozen python -m pitchvolt.narrative_eval` to print a deterministic JSON report. The scenario corpus is original synthetic football evidence, with valid structured facts, an invalid metric, mismatched evidence, and **plausible structured facts accompanied by fabricated goal/possession text**. Report fields include counts by verdict and an explicit `semantic_verification: not_implemented` marker. All candidates remain `publishable=false`.

This benchmark tests **claim validation and fail-closed publication policy**, not semantic entailment, model quality, inference latency, or hallucination detection within the raw text. It is deliberately no-cost and does not use Foundry. A future real-model benchmark should measure sampled candidate outputs and manual annotations separately, without treating this four-case synthetic fixture as an accuracy estimate.

## Next locally authorized live evaluation: observable decisions and shadow prose

After explicit PR review and merge, one operator-approved invocation of `python -m pitchvolt.foundry_smoke` will request the existing two model roles only. The Analyst returns a structured plan and all canonical evidence must be retrieved through the read-only tool. Storyteller returns a structured selection and, optionally, `authored_headline` and `authored_text` as **untrusted, shadow-only proposals**. The backend continues to publish the prior deterministic verified narrative, ignoring these model-authored fields. The shadow evaluator classifies the proposal as unverified and never grants publication.

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

Versioned agent initialization instructions are defined in `src/pitchvolt/agent_policies.py` (`grounded-v1`). The Analyst's stable policy requires exhaustive read-only evidence inspection, exact IDs and no invented player or outcome facts. The Storyteller's stable policy defines audience-aware output, prohibits unsupported tactical superlatives and requires verbatim selection from the two reviewed headline/text variants for the local safety experiment. An Editorial policy is defined but Editorial inference is not invoked. Actual match evidence, approved options and output schemas are supplied **per request**; there are no long-running agents, persistent model memory or hidden coaching requests. Policy tests run entirely offline. Prompt discipline improves reliability but does not provide semantic proof of arbitrary prose; the bounded grammar gate and deterministic public renderer remain authoritative.

## Research-based role and audience policy architecture (grounded-v2)

The policy architecture follows Microsoft guidance for precise actionable agent roles, sequential handoff, explicit grounding constraints, documented abstention/fallback, structured outputs and versioned testable instructions. Stable agent instructions are built once at initialization. A per-invocation, typed `Audience` profile is injected into the Storyteller's task context; immutable verified match evidence is passed separately. Current flavors:
- **Casual**: accessible, lively, plain-language explanation of the documented moment; never sensationalize a single sequence.
- **Analyst**: technical, quantitative interpretation with seconds, tactical classification and attacking-action count; observed facts must not become unsupported causal claims.
- **Club**: pragmatic, team-oriented learning focus without falsely attributing intent, coaching instructions or comparative dominance.

Shared `CORE_POLICY` requires synthetic-data disclosure, ignores instructions embedded in untrusted event data, forbids invented scores, players and match-long superiority, and routes outputs back into typed contracts. Analyst and Storyteller explicitly act as **internal subagents**, never public responders. Editorial is an unscheduled future reviewer, not an extra inference call or a replacement for backend verification. Unknown audience flavors fail closed. These constraints are enforced by the server as applicable; instructions improve behavior but are not a security boundary.

Policy references (retrieved October 2026):
- Microsoft Azure Architecture Center, grounding, fallback, source citation, separation of instructions/context and prompt versioning: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-prompt-engineering
- Microsoft Agent Framework, sequential specialized agents: https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/sequential
- Microsoft Copilot Studio multi-agent best practices, clear subagent identity and single final publisher: https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/multi-agent-patterns
- Microsoft Cloud Adoption Framework, instruction configuration/versioning and structured outputs: https://github.com/MicrosoftDocs/cloud-adoption-framework/blob/main/docs/ai-agents/build-secure-process.md
- Microsoft Foundry evaluators, groundedness, relevance, task adherence and abstention: https://github.com/MicrosoftDocs/azure-ai-docs/blob/main/articles/foundry/concepts/evaluation-evaluators/agent-evaluators.md

Future expansion: separate free-form creativity/evidence-linked atomic claim extraction from the bounded publishing mode, then evaluate precision, groundedness, abstention, latency, and hallucination rate on a frozen fixture set before enabling public model prose. Do not confuse passing the finite grammar with semantic entailment.

## Live Analyst exhaustion and retry policy

The fourth authorized smoke attempt retrieved six events but GPT-5 mini finished with `finish_reason=length` and `AgentResponse.value=None` under the 512-token Analyst output cap; the Storyteller was never called and the deterministic fallback remained correct. In reasoning models, hidden reasoning tokens count toward the output budget. This is evidence of output truncation, not evidence of faulty input facts. The exact token count remains unknown until SDK usage extraction is fixed.

The isolated live smoke now budgets **4096 Analyst output tokens** and leaves Storyteller at its configured 256-token default. The configurable `RoleSettings` validation ceiling is **8192 tokens**, but general application defaults stay unchanged. No additional inference was made during development. The smoke restores the OpenAI Python SDK default of **two retries** for eligible transport/HTTP errors (network, 408, 409, 429, 5xx), with backoff; there are **zero role-level retries** after a `length` finish or invalid schema. See https://github.com/openai/openai-python#retries and https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/reasoning for the SDK retry policy and reasoning-token behavior.

Retries are not free: one logical agent run can perform multiple tool/model requests; each retry can increase billing, and the maximum role count is not a hard cap on HTTP requests or euros spent. Available trial credits are not a spending authorization. An operator must separately approve the next one-time billable execution after reviewing this change. Timeout remains 15 seconds per role; `length` is explicitly not auto-retried.

## Configuration ownership and DRY review

All **Foundry Python inference defaults, caps, smoke deployments, output budgets, retry limits and timeout settings** are now owned by `src/pitchvolt/foundry_config.py`. The frozen `SMOKE_SETTINGS` controls both the isolated CLI and manual Foundry preview, and `isolated_foundry_config()` constructs the effective validated `FoundryConfig` for both. The preview and smoke are explicitly opt-in separately; configuration construction never grants inference approval. The CLI reports effective settings rather than redeclaring them. The SDK's two eligible transient transport retries are distinct from role-level retries, which remain disabled.

DRY audit scope: inspected `foundry_config.py`, `foundry_smoke.py`, `foundry_preview.py`, `foundry_adapter.py`, the role policy module, and relevant SDK/smoke/preview tests. Eliminated duplicated deployment IDs, smoke Analyst token values, repeated per-route FoundryConfig construction, max tool-call and timeout literals, and corresponding test references. **This is not yet an exhaustive whole-repository DRY certification**: Python orchestration, front-end settings, documentation examples and additional application areas require their own audit against the project's DRY rule. Tests intentionally keep hard-coded expected values to detect accidental behavior/config changes.

## Real-model optional composition contract regression

The fifth authorized live experiment (after #50) confirmed 6/6 Analyst evidence tool calls, structured Analyst and Storyteller responses, and an evidence-derived Storyteller headline/text candidate eligible under the finite reviewed grammar. Nevertheless, the Storyteller returned `fact_order=["transition", "actions"]`; `publish_controlled` correctly rejected the incomplete list and used a deterministic fallback. The independent `bounded_grounding.eligible=true` does not override the publication contract or imply overall success. No new inference was performed in this PR.

This update aligns the Storyteller initialization policy and per-request instructions around one existing source of truth (`FactSlot`): `fact_order` is optional and must be `null` or a complete permutation of every canonical fact slot. The required slot names are generated directly from the enum, not copied into an unrelated prompt constant. The backend keeps its existing strict verification, including rejection of subsets, duplicates, and unrecognized slots. The next separately approved live test should verify the generated selection either omits ordering or includes all four slots, and should still treat free-form model prose as shadow-only. Token usage telemetry remains unavailable.

## Evidence-linked original-prose shadow experiment

The next research increment permits the Storyteller to propose **original** headline/commentary pairs, rather than choosing only finite approved variants. This is still **shadow-only**: neither `publish_controlled` nor `verify_narrative` is changed to trust free-form prose. The existing strict controlled renderer and deterministic fallback remain authoritative.

Optional `StorytellerSelection.evidence_links` consists of immutable `LinkedClaim` objects with a typed claim, an exact excerpt from the headline or text, and one or more cited evidence-event IDs. `assess_evidence_links` checks that the claim manifest matches the canonical insight, links cover every declared claim, excerpts occur in the proposed text, and cited IDs belong to the immutable evidence bundle. It returns `linked_shadow_not_semantically_verified` only as **provenance metadata**, with `publishable=false` unconditionally.

**Crucial limitation:** a claim-to-excerpt link does not imply textual entailment, and the generated text might contain unsupported assertions elsewhere (including scoreline, outcome, superiority or causal claims). Even an apparent pass must never publish arbitrary model text. A future *independent* claim extraction / entailment review, coverage assessment for every material assertion, editorial abstention and adversarial evaluation are prerequisites for expanding publication beyond the existing bounded grammar. All additions here are offline/opt-in and do not enable Azure inference.

The optional link schema resides in one backend module and reuses the existing `Claim`, `EvidenceBundle` and event IDs, avoiding parallel evidence schemas. Existing bounded grammar tests and behavior remain in place.

## Conservative assertion audit (shadow only)

An independent offline lexical auditor flags a deliberately limited set of football assertions: attacking-action counts, turnover-to-shot duration, scorelines and selected outcome/identity/superiority language. It reports supported, contradicted or unverifiable per recognized excerpt. This is not semantic entailment or full assertion extraction: coverage is **always incomplete**, even if every identified numerical claim matches canonical metrics. No audit result authorizes publication. The public narrative and deterministic fallback remain unchanged. A later milestone requires comprehensive claim extraction and independent entailment evaluation with adversarial coverage tests before any creative prose publication.

## Broadcast voice, shadow only

The Casual editorial policy prioritizes passionate, spontaneous live-play-by-play phrasing inspired by the energy of Premier League commentary, without imitating named broadcasters. Analyst is an energetic but precise co-commentator; Club is engaged but evidence-first. This is a **prompt policy change only**: model-authored text remains shadow-only, and the controlled renderer still determines the public narrative. Synthetic match events must not become fabricated goals, scorelines, crowd responses or match outcomes. No Azure inference is enabled by this change.
