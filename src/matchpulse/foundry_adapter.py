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
        if not self.model_deployment.strip():
            raise ValueError("Foundry deployment name is required")


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
        client = FoundryChatClient(
            project_endpoint=config.project_endpoint,
            model=config.model_deployment,
            credential=DefaultAzureCredential(),
        )
        self._max_output_tokens = config.max_output_tokens_per_role
        self.last_evidence_tool_calls: tuple[str, ...] = ()
        self._analyst = Agent(
            client=client,
            name="MatchPulseAnalyst",
            instructions=(
                "Analyze ONLY the provided immutable football evidence. "
                "Choose a tactical angle and copy the exact insight/evidence IDs. "
                "Never infer metrics or invent events. Output only the requested schema."
            ),
        )
        self._storyteller = Agent(
            client=client,
            name="MatchPulseStoryteller",
            instructions=(
                "Select a presentation style for the requested audience using the "
                "Analyst's validated angle. Copy the insight ID and angle exactly. "
                "Do not generate prose or football numbers; the application renders text."
            ),
        )

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
