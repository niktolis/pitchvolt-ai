"""Role handoff and fail-closed publication tests. No remote inference."""
import asyncio
from dataclasses import dataclass

import pytest

from matchpulse.intelligence import analyze_stream
from matchpulse.narrative import Audience, EvidenceBundle, InMemoryEvidenceTool
from matchpulse.scenarios import scenario
from matchpulse.workflow import (
    Angle, AnalystPlan, Orchestrator, StorytellerSelection, Style,
    publish_controlled,
)


def _bundle() -> EvidenceBundle:
    match, events = scenario("high_press")
    insight = analyze_stream(match, events)[0]
    lookup = {event.event_id: event for event in events}
    return EvidenceBundle(insight, tuple(lookup[eid] for eid in insight.evidence_event_ids))


@dataclass
class AnalystDouble:
    invalid: bool = False

    async def analyze(self, evidence: EvidenceBundle) -> AnalystPlan:
        return AnalystPlan(
            insight_id=evidence.insight.insight_id,
            angle=Angle.TACTICAL,
            evidence_event_ids=(
                ("fake-id",) if self.invalid else evidence.insight.evidence_event_ids
            ),
        )


@dataclass
class StorytellerDouble:
    mismatch: bool = False

    async def select(
        self, plan: AnalystPlan, evidence: EvidenceBundle, audience: Audience
    ) -> StorytellerSelection:
        return StorytellerSelection(
            insight_id=plan.insight_id,
            angle=Angle.TRANSITION if self.mismatch else plan.angle,
            style=Style.TECHNICAL,
            audience=audience,
        )


def test_handoff_renders_only_server_owned_fact_templates() -> None:
    bundle = _bundle()
    tool = InMemoryEvidenceTool(lambda _: bundle)
    result = asyncio.run(Orchestrator(tool, AnalystDouble(), StorytellerDouble()).narrate(
        bundle.insight.insight_id, Audience.ANALYST
    ))
    assert result.source == "controlled"
    assert result.rejection_reason is None
    assert [step.role for step in result.trace] == [
        "evidence", "analyst", "storyteller", "verifier",
    ]
    assert result.narrative.insight_id == bundle.insight.insight_id
    assert f"{bundle.insight.metrics['attacking_actions']} attacking actions" in result.narrative.text
    assert result.narrative.evidence_event_ids == bundle.insight.evidence_event_ids


@pytest.mark.parametrize(("analyst_bad", "storyteller_bad"), [(True, False), (False, True)])
def test_invalid_handoff_falls_back_without_publishing_ai_prose(
    analyst_bad: bool, storyteller_bad: bool,
) -> None:
    bundle = _bundle()
    flow = Orchestrator(
        InMemoryEvidenceTool(lambda _: bundle),
        AnalystDouble(invalid=analyst_bad),
        StorytellerDouble(mismatch=storyteller_bad),
    )
    result = asyncio.run(flow.narrate(bundle.insight.insight_id, Audience.CASUAL))
    assert result.source == "fallback"
    assert result.rejection_reason
    assert result.narrative.insight_id == bundle.insight.insight_id
    assert result.trace[-1].action == "reject"


def test_storyteller_cannot_change_insight_or_angle() -> None:
    bundle = _bundle()
    plan = AnalystPlan(
        insight_id=bundle.insight.insight_id,
        angle=Angle.TRANSITION,
        evidence_event_ids=bundle.insight.evidence_event_ids,
    )
    decision = StorytellerSelection(
        insight_id="made-up", audience=Audience.CASUAL,
        angle=Angle.TRANSITION, style=Style.CONCISE,
    )
    with pytest.raises(ValueError, match="insight"):
        publish_controlled(decision, plan, bundle)
