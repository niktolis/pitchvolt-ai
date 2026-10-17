"""Optional Microsoft Agent Framework Foundry project inference provider.

Importing this module never creates a client, authenticates or sends requests.
Runtime inference requires a separate explicit operator opt-in and an installed
optional SDK. It is not activated by the application by default.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter

from matchpulse.agent_policies import (
    ANALYST_INSTRUCTIONS,
    EDITORIAL_INSTRUCTIONS,
    STORYTELLER_INSTRUCTIONS,
)
from matchpulse.foundry_config import FoundryConfig, RoleSettings
from matchpulse.grounded_prose import GroundingResult, approved_phrasings, assess_grounded_prose
from matchpulse.narrative import Audience, Claim, ClaimKind, EvidenceBundle, NarrativeCandidate
from matchpulse.shadow_validation import ShadowAssessment, assess_candidate
from matchpulse.workflow import AnalystPlan, StorytellerSelection

__all__ = ["FoundryConfig", "FoundryDisabled", "FoundryRoles", "RoleInvocation", "RoleSettings"]


@dataclass(frozen=True)
class RoleInvocation:
    role: str
    deployment: str
    duration_ms: float
    input_tokens: int | None
    output_tokens: int | None


def usage_counts(response: object) -> tuple[int | None, int | None]:
    """Read allowlisted usage fields, never prompts or raw model text."""
    def get(obj: object, name: str) -> object:
        return obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)

    containers = [response]
    for name in ("usage", "usage_details", "raw_response"):
        item = get(response, name)
        if item is not None:
            containers.append(item)
            nested = get(item, "usage")
            if nested is not None:
                containers.append(nested)
    messages = get(response, "messages")
    if isinstance(messages, (tuple, list)):
        for message in messages:
            for name in ("usage", "usage_details"):
                item = get(message, name)
                if item is not None:
                    containers.append(item)

    def count(obj: object, names: tuple[str, ...]) -> int | None:
        for name in names:
            value = get(obj, name)
            if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100_000_000:
                return value
        return None

    for container in containers:
        input_count = count(container, ("input_tokens", "prompt_tokens"))
        output_count = count(container, ("output_tokens", "completion_tokens"))
        if input_count is not None or output_count is not None:
            return input_count, output_count
    return None, None


class FoundryDisabled(RuntimeError):
    """Provider access deliberately blocked until inference opt-in."""


def sanitized_response_metadata(response: object) -> dict[str, object]:
    """Allowlisted response metadata only; no generated text or provider payload."""
    allowed = {"stop", "length", "tool_calls", "content_filter", "completed", "incomplete", "max_output_tokens", "end_turn"}
    def reason(value: object) -> str | None:
        return value if isinstance(value, str) and value in allowed else None

    input_count, output_count = usage_counts(response)

    messages = getattr(response, "messages", None)
    if not isinstance(messages, (list, tuple)):
        messages = ()
    return {
        "response_type": type(response).__name__,
        "structured_value_present": getattr(response, "value", None) is not None,
        "finish_reason": reason(getattr(response, "finish_reason", None)),
        "response_status": reason(getattr(response, "status", None)),
        "input_tokens": input_count,
        "output_tokens": output_count,
        "total_tokens": input_count + output_count if input_count is not None and output_count is not None else None,
        "message_count": min(len(messages), 1000),
    }


class FoundryRoles:
    """Two specialized ephemeral roles; no server-hosted agent resources."""

    def __init__(
        self, config: FoundryConfig, *, credential: object | None = None,
        project_client: object | None = None,
    ) -> None:
        if not config.inference_explicitly_approved:
            raise FoundryDisabled("Model inference is disabled pending cost approval")
        # Imports and credential construction occur only in approved runtime mode.
        try:
            from agent_framework import Agent
            from agent_framework.foundry import FoundryChatClient
            from azure.identity import DefaultAzureCredential
        except ImportError as exc:
            raise FoundryDisabled(
                "Install the reviewed agent-framework-foundry SDK before enabling inference"
            ) from exc
        # One credential, independently configured clients per specialist.
        # Editorial may be constructed for configuration validation, but is not
        # invoked by the two-role orchestrator or included in the call budget.
        if credential is None:
            credential = DefaultAzureCredential()
        clients = {
            role: FoundryChatClient(
                project_endpoint=config.project_endpoint,
                model=deployment,
                credential=credential,
                **({"project_client": project_client} if project_client is not None else {}),
            )
            for role, deployment in config.role_deployments.items()
        }
        self._config = config
        self.invocations: list[RoleInvocation] = []
        self._attempts = {'analyst': 0, 'storyteller': 0}
        self.last_attempted_role: str | None = None
        self.last_evidence_tool_calls: tuple[str, ...] = ()
        self.last_response_metadata: dict[str, object] | None = None
        self.role_decisions: dict[str, dict[str, object]] = {}
        self.role_response_metadata: dict[str, dict[str, object]] = {}
        self.last_shadow_assessment: ShadowAssessment | None = None
        self.last_authored_candidate: NarrativeCandidate | None = None
        self.last_grounding_result: GroundingResult | None = None
        instructions = {
            "analyst": ANALYST_INSTRUCTIONS,
            "storyteller": STORYTELLER_INSTRUCTIONS,
            "editorial": EDITORIAL_INSTRUCTIONS,
        }
        self._agents = {
            role: Agent(
                client=clients[role],
                name=f"MatchPulse{role.title()}",
                instructions=instructions[role],
            )
            for role in clients
        }
        self._analyst = self._agents["analyst"]
        self._storyteller = self._agents["storyteller"]
        # Intentionally no Editorial invocation or escalation policy yet.

    async def _invoke(self, role: str, prompt: str, schema: type, tools: list | None = None) -> object:
        if role not in self._attempts or self._attempts[role] >= 1:
            raise FoundryDisabled('Role call budget exhausted or not approved')
        if len(prompt) > self._config.max_prompt_characters:
            raise ValueError('Prompt exceeds character cap')
        settings = self._config.settings_for(role)
        options: dict[str, object] = {
            "response_format": schema,
            "max_tokens": settings.max_output_tokens,
        }
        # GPT-5-specific reasoning options must be verified against the
        # installed SDK before being sent to Foundry. Fail closed for now.
        if settings.reasoning_effort is not None:
            raise FoundryDisabled("Reasoning effort requires SDK compatibility validation")
        started = perf_counter()
        self._attempts[role] += 1
        self.last_attempted_role = role
        response = await asyncio.wait_for(
            self._agents[role].run(prompt, options=options, **({"tools": tools} if tools is not None else {})),
            timeout=self._config.timeout_seconds_per_role,
        )
        self.last_response_metadata = sanitized_response_metadata(response)
        self.role_response_metadata[role] = self.last_response_metadata
        input_count, output_count = usage_counts(response)
        self.invocations.append(RoleInvocation(
            role, self._config.role_deployments[role],
            (perf_counter() - started) * 1000,
            input_count, output_count,
        ))
        return response

    async def analyze(self, evidence: EvidenceBundle) -> AnalystPlan:
        insight = evidence.insight
        observed: list[str] = []
        allowed = {event.event_id: event for event in evidence.events}

        def get_evidence_event(event_id: str) -> str:
            """Retrieve a validated synthetic event by ID from this insight only."""
            if len(observed) >= self._config.max_tool_calls_per_analyst:
                raise ValueError("Analyst tool-call cap exceeded")
            event = allowed.get(event_id)
            if event is None:
                raise ValueError("Event is not evidence for this insight")
            observed.append(event_id)
            return event.model_dump_json()

        self.last_evidence_tool_calls = ()
        response = await self._invoke("analyst",
            f"Insight: {insight.insight_id}\n"
            f"Kind: {insight.kind.value}\n"
            f"Events: {list(insight.evidence_event_ids)}\n"
            f"Metrics: {insight.metrics}\n"
            "Return a structured plan and preserve all IDs exactly.",
            AnalystPlan,
            tools=[get_evidence_event],
        )
        self.last_evidence_tool_calls = tuple(observed)
        if response.value is None:
            raise ValueError("Analyst returned no structured output")
        plan = AnalystPlan.model_validate(response.value)
        if plan.evidence_event_ids != insight.evidence_event_ids:
            raise ValueError("Analyst supplied unverified evidence IDs")
        if set(observed) != set(insight.evidence_event_ids):
            raise ValueError("Analyst did not retrieve all verified evidence events")
        self.role_decisions["analyst"] = plan.model_dump(mode="json")
        return plan

    async def select(
        self, plan: AnalystPlan, evidence: EvidenceBundle, audience: Audience
    ) -> StorytellerSelection:
        response = await self._invoke("storyteller",
            f"Requested audience: {audience.value}\n"
            f"Approved Analyst plan: {plan.model_dump_json()}\n"
            f"Verified team: {evidence.insight.team_id}; tactic: {evidence.insight.kind.value}; "
            f"duration_ms: {evidence.insight.metrics['transition_duration_ms']}; "
            f"attacking_actions: {evidence.insight.metrics['attacking_actions']}. "
            "Select a supported style and fact_order; separately propose authored_headline and "
            "authored_text using ONLY these verified facts. This proposal will NOT be published.\n"
            f"Approved headline/text pairs: {approved_phrasings(evidence)!r}. "
            "Choose one complete pair verbatim; do not add qualifiers or extra sentences.",
            StorytellerSelection,
        )
        if response.value is None:
            raise ValueError("Storyteller returned no structured output")
        selection = StorytellerSelection.model_validate(response.value)
        self.role_decisions["storyteller"] = selection.model_dump(
            mode="json", exclude={"authored_headline", "authored_text"}
        )
        if selection.authored_headline and selection.authored_text:
            insight = evidence.insight
            self.last_authored_candidate = NarrativeCandidate(
                insight_id=insight.insight_id,
                audience=audience,
                headline=selection.authored_headline,
                text=selection.authored_text,
                evidence_event_ids=insight.evidence_event_ids,
                claims=(
                    Claim(kind=ClaimKind.INSIGHT_KIND, key="kind", value=insight.kind.value),
                    Claim(kind=ClaimKind.TEAM_ID, key="team_id", value=insight.team_id),
                    Claim(kind=ClaimKind.METRIC, key="transition_duration_ms",
                          value=insight.metrics["transition_duration_ms"]),
                    Claim(kind=ClaimKind.METRIC, key="attacking_actions",
                          value=insight.metrics["attacking_actions"]),
                ),
            )
            self.last_shadow_assessment = assess_candidate(
                self.last_authored_candidate, evidence
            )
            self.last_grounding_result = assess_grounded_prose(
                self.last_authored_candidate, evidence
            )
        return selection
