"""Optional Microsoft Agent Framework Foundry project inference provider.

Importing this module never creates a client, authenticates or sends requests.
Runtime inference requires a separate explicit operator opt-in and an installed
optional SDK. It is not activated by the application by default.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter
from urllib.parse import urlsplit

from matchpulse.narrative import Audience, EvidenceBundle
from matchpulse.workflow import AnalystPlan, StorytellerSelection


@dataclass(frozen=True)
class RoleSettings:
    max_output_tokens: int = 256
    reasoning_effort: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.max_output_tokens <= 1024:
            raise ValueError("Per-role output token cap must be between 1 and 1024")
        if self.reasoning_effort not in (None, "low", "medium", "high"):
            raise ValueError("Unsupported reasoning effort")


@dataclass(frozen=True)
class RoleInvocation:
    role: str
    deployment: str
    duration_ms: float
    input_tokens: int | None
    output_tokens: int | None


@dataclass(frozen=True)
class FoundryConfig:
    project_endpoint: str
    model_deployment: str
    inference_explicitly_approved: bool = False
    max_output_tokens_per_role: int = 256
    storyteller_model_deployment: str | None = None
    editorial_model_deployment: str | None = None
    max_inference_calls_per_narrative: int = 2
    analyst_settings: RoleSettings | None = None
    storyteller_settings: RoleSettings | None = None
    editorial_settings: RoleSettings | None = None
    max_tool_calls_per_analyst: int = 12
    max_prompt_characters: int = 12000
    timeout_seconds_per_role: float = 6.0

    def __post_init__(self) -> None:
        parsed = urlsplit(self.project_endpoint)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Foundry endpoint must be a clean HTTPS project URL")
        if not parsed.hostname.endswith(".services.ai.azure.com"):
            raise ValueError("Foundry endpoint must target the Foundry project domain")
        RoleSettings(max_output_tokens=self.max_output_tokens_per_role)
        if not 1 <= self.max_tool_calls_per_analyst <= 32:
            raise ValueError('Tool-call cap must be between 1 and 32')
        if not 256 <= self.max_prompt_characters <= 16000:
            raise ValueError('Prompt cap must be between 256 and 16000')
        if not 0.1 <= self.timeout_seconds_per_role <= 15:
            raise ValueError('Role timeout must be between 0.1 and 15 seconds')
        if self.max_inference_calls_per_narrative != 2:
            raise ValueError("Two-role narrative must have exactly two inference calls")
        for deployment in (
            self.model_deployment,
            self.storyteller_model_deployment,
            self.editorial_model_deployment,
        ):
            if deployment is not None and not deployment.strip():
                raise ValueError("Foundry deployment name is required")

    def settings_for(self, role: str) -> RoleSettings:
        if role not in ("analyst", "storyteller", "editorial"):
            raise ValueError("Unknown specialist role")
        custom = getattr(self, f"{role}_settings")
        return custom if custom is not None else RoleSettings(
            max_output_tokens=self.max_output_tokens_per_role
        )

    @property
    def role_deployments(self) -> dict[str, str]:
        """Configured clients; Editorial is prepared but never scheduled."""
        return {
            "analyst": self.model_deployment,
            "storyteller": self.storyteller_model_deployment or self.model_deployment,
            **(
                {"editorial": self.editorial_model_deployment}
                if self.editorial_model_deployment is not None
                else {}
            ),
        }


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
