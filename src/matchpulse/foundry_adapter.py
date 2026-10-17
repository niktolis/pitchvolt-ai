"""Optional Microsoft Agent Framework Foundry project inference provider.

Importing this module never creates a client, authenticates or sends requests.
Runtime inference requires a separate explicit operator opt-in and an installed
optional SDK. It is not activated by the application by default.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from matchpulse.narrative import Audience, EvidenceBundle
from matchpulse.workflow import AnalystPlan, StorytellerSelection


@dataclass(frozen=True)
class FoundryConfig:
    project_endpoint: str
    model_deployment: str
    inference_explicitly_approved: bool = False
    max_output_tokens_per_role: int = 256
    storyteller_model_deployment: str | None = None
    editorial_model_deployment: str | None = None
    max_inference_calls_per_narrative: int = 2

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
        if not 1 <= self.max_output_tokens_per_role <= 1024:
            raise ValueError("Per-role output token cap must be between 1 and 1024")
        if self.max_inference_calls_per_narrative != 2:
            raise ValueError("Two-role narrative must have exactly two inference calls")
        for deployment in (
            self.model_deployment,
            self.storyteller_model_deployment,
            self.editorial_model_deployment,
        ):
            if deployment is not None and not deployment.strip():
                raise ValueError("Foundry deployment name is required")

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
        self._max_output_tokens = config.max_output_tokens_per_role
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

    async def analyze(self, evidence: EvidenceBundle) -> AnalystPlan:
        insight = evidence.insight
        observed: list[str] = []
        allowed = {event.event_id: event for event in evidence.events}

        def get_evidence_event(event_id: str) -> str:
            """Retrieve a validated synthetic event by ID from this insight only."""
            event = allowed.get(event_id)
            if event is None:
                raise ValueError("Event is not evidence for this insight")
            observed.append(event_id)
            return event.model_dump_json()

        self.last_evidence_tool_calls = ()
        response = await self._analyst.run(
            f"Insight: {insight.insight_id}\n"
            f"Kind: {insight.kind.value}\n"
            f"Events: {list(insight.evidence_event_ids)}\n"
            f"Metrics: {insight.metrics}\n"
            "Return a structured plan and preserve all IDs exactly.",
            options={
                "response_format": AnalystPlan,
                "max_output_tokens": self._max_output_tokens,
                "tools": [get_evidence_event],
            },
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
        response = await self._storyteller.run(
            f"Requested audience: {audience.value}\n"
            f"Approved Analyst plan: {plan.model_dump_json()}\n"
            "Choose an allowed style and preserve the evidence-grounded angle.",
            options={
                "response_format": StorytellerSelection,
                "max_output_tokens": self._max_output_tokens,
            },
        )
        if response.value is None:
            raise ValueError("Storyteller returned no structured output")
        return StorytellerSelection.model_validate(response.value)
