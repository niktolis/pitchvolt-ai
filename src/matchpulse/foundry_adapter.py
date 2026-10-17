"""Optional Microsoft Agent Framework Foundry project inference provider.

Importing this module never creates a client, authenticates or sends requests.
Runtime inference requires a separate explicit operator opt-in and an installed
optional SDK. It is not activated by the application by default.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter

from matchpulse.foundry_config import FoundryConfig, RoleSettings
from matchpulse.narrative import Audience, EvidenceBundle
from matchpulse.workflow import AnalystPlan, StorytellerSelection

__all__ = ["FoundryConfig", "FoundryDisabled", "FoundryRoles", "RoleInvocation", "RoleSettings"]


@dataclass(frozen=True)
class RoleInvocation:
    role: str
    deployment: str
    duration_ms: float
    input_tokens: int | None
    output_tokens: int | None


class FoundryDisabled(RuntimeError):
    """Provider access deliberately blocked until inference opt-in."""


class FoundryRoles:
    """Two specialized ephemeral roles; no server-hosted agent resources."""

    def __init__(self, config: FoundryConfig) -> None:
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
        credential = DefaultAzureCredential()
        clients = {
            role: FoundryChatClient(
                project_endpoint=config.project_endpoint,
                model=deployment,
                credential=credential,
            )
            for role, deployment in config.role_deployments.items()
        }
        self._config = config
        self.invocations: list[RoleInvocation] = []
        self._attempts = {'analyst': 0, 'storyteller': 0}
        self.last_evidence_tool_calls: tuple[str, ...] = ()
        instructions = {
            "analyst": (
                "Analyze ONLY immutable football evidence. Use provided read-only "
                "tools to inspect each cited event. Preserve evidence IDs and metrics; "
                "return only the structured tactical plan."
            ),
            "storyteller": (
                "Choose audience-specific style from the validated Analyst plan. "
                "Preserve insight ID and angle. Never generate football claims or prose."
            ),
            "editorial": (
                "Review only explicitly escalated, already grounded interpretations. "
                "Never override the deterministic factual verifier."
            ),
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
            "max_output_tokens": settings.max_output_tokens,
        }
        # GPT-5-specific reasoning options must be verified against the
        # installed SDK before being sent to Foundry. Fail closed for now.
        if settings.reasoning_effort is not None:
            raise FoundryDisabled("Reasoning effort requires SDK compatibility validation")
        if tools is not None:
            options["tools"] = tools
        started = perf_counter()
        self._attempts[role] += 1
        response = await asyncio.wait_for(
            self._agents[role].run(prompt, options=options),
            timeout=self._config.timeout_seconds_per_role,
        )
        usage = getattr(response, "usage", None)
        def token_count(name: str) -> int | None:
            value = getattr(usage, name, None)
            return value if isinstance(value, int) and value >= 0 else None
        self.invocations.append(RoleInvocation(
            role, self._config.role_deployments[role],
            (perf_counter() - started) * 1000,
            token_count("input_tokens"), token_count("output_tokens"),
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
        return plan

    async def select(
        self, plan: AnalystPlan, evidence: EvidenceBundle, audience: Audience
    ) -> StorytellerSelection:
        response = await self._invoke("storyteller",
            f"Requested audience: {audience.value}\n"
            f"Approved Analyst plan: {plan.model_dump_json()}\n"
            "Choose an allowed style and preserve the evidence-grounded angle.",
            StorytellerSelection,
        )
        if response.value is None:
            raise ValueError("Storyteller returned no structured output")
        return StorytellerSelection.model_validate(response.value)
