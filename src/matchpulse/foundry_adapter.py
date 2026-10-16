"""Optional Microsoft Agent Framework Foundry project inference provider.

Importing this module never creates a client, authenticates or sends requests.
Runtime inference requires a separate explicit operator opt-in and an installed
optional SDK. It is not activated by the application by default.
"""
from __future__ import annotations

from dataclasses import dataclass

from matchpulse.narrative import Audience, EvidenceBundle
from matchpulse.workflow import AnalystPlan, StorytellerSelection


@dataclass(frozen=True)
class FoundryConfig:
    project_endpoint: str
    model_deployment: str
    inference_explicitly_approved: bool = False

    def __post_init__(self) -> None:
        if not self.project_endpoint.startswith("https://"):
            raise ValueError("Foundry endpoint must be HTTPS")
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
        response = await self._analyst.run(
            f"Insight: {insight.insight_id}\n"
            f"Kind: {insight.kind.value}\n"
            f"Events: {list(insight.evidence_event_ids)}\n"
            f"Metrics: {insight.metrics}\n"
            "Return a structured plan and preserve all IDs exactly.",
            options={"response_format": AnalystPlan},
        )
        if response.value is None:
            raise ValueError("Analyst returned no structured output")
        return AnalystPlan.model_validate(response.value)

    async def select(
        self, plan: AnalystPlan, evidence: EvidenceBundle, audience: Audience
    ) -> StorytellerSelection:
        response = await self._storyteller.run(
            f"Requested audience: {audience.value}\n"
            f"Approved Analyst plan: {plan.model_dump_json()}\n"
            "Choose an allowed style and preserve the evidence-grounded angle.",
            options={"response_format": StorytellerSelection},
        )
        if response.value is None:
            raise ValueError("Storyteller returned no structured output")
        return StorytellerSelection.model_validate(response.value)
