"""Role handoff and fail-closed publication tests. No remote inference."""
import asyncio
from dataclasses import dataclass

import pytest

from pitchvolt.intelligence import analyze_stream
from pitchvolt.narrative import Audience, EvidenceBundle, InMemoryEvidenceTool
from pitchvolt.scenarios import scenario
from pitchvolt.workflow import (
    AnalystPlan,
    Angle,
    FactSlot,
    Orchestrator,
    StorytellerSelection,
    Style,
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
    assert result.trace[0].role == "evidence"
    evidence_steps = [s for s in result.trace if s.action == "get_event"]
    assert [s.reference for s in evidence_steps] == list(bundle.insight.evidence_event_ids)
    assert all(s.role == "evidence" and s.duration_ms >= 0 for s in evidence_steps)
    assert [s.role for s in result.trace[-3:]] == [
        "analyst", "storyteller", "verifier",
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


def test_evidence_tool_rejects_fabricated_event_reference() -> None:
    bundle = _bundle()
    tool = InMemoryEvidenceTool(lambda _: bundle)
    with pytest.raises(ValueError, match="not evidence"):
        tool.get_event(bundle.insight.insight_id, "invented-event-id")


def test_event_tool_failure_prevents_controlled_publication() -> None:
    bundle = _bundle()

    class MissingEventTool:
        def get(self, insight_id: str) -> EvidenceBundle:
            assert insight_id == bundle.insight.insight_id
            return bundle

        def get_event(self, insight_id: str, event_id: str):
            raise ValueError("event unavailable")

    flow = Orchestrator(MissingEventTool(), AnalystDouble(), StorytellerDouble())
    result = asyncio.run(flow.narrate(bundle.insight.insight_id, Audience.ANALYST))
    assert result.source == "fallback"
    assert result.trace[-1].action == "reject"
    assert result.narrative.evidence_event_ids == bundle.insight.evidence_event_ids


def test_model_controls_fact_order_but_not_factual_values() -> None:
    bundle = _bundle()
    plan = AnalystPlan(
        insight_id=bundle.insight.insight_id,
        angle=Angle.TACTICAL,
        evidence_event_ids=bundle.insight.evidence_event_ids,
    )
    decision = StorytellerSelection(
        insight_id=plan.insight_id,
        audience=Audience.CASUAL,
        angle=plan.angle,
        style=Style.CONCISE,
        fact_order=(FactSlot.ACTIONS, FactSlot.TEAM, FactSlot.TRANSITION, FactSlot.TACTIC),
    )
    narrative = publish_controlled(decision, plan, bundle)
    assert narrative.text.startswith(
        f"Attacking actions: {bundle.insight.metrics['attacking_actions']} · "
        f"Team: {bundle.insight.team_id}"
    )
    seconds = bundle.insight.metrics["transition_duration_ms"] / 1000
    assert f"Turnover-to-shot: {seconds:.3f}s" in narrative.text
    assert narrative.evidence_event_ids == bundle.insight.evidence_event_ids


@pytest.mark.parametrize("order", [
    (),
    (FactSlot.TEAM, FactSlot.TEAM, FactSlot.TRANSITION, FactSlot.ACTIONS),
    (FactSlot.TEAM, FactSlot.TACTIC, FactSlot.TRANSITION),
])
def test_incomplete_or_duplicate_model_composition_rejected(order) -> None:
    bundle = _bundle()
    plan = AnalystPlan(
        insight_id=bundle.insight.insight_id,
        angle=Angle.TACTICAL,
        evidence_event_ids=bundle.insight.evidence_event_ids,
    )
    decision = StorytellerSelection(
        insight_id=plan.insight_id,
        audience=Audience.ANALYST,
        angle=plan.angle,
        style=Style.TECHNICAL,
        fact_order=order,
    )
    with pytest.raises(ValueError, match="each canonical fact exactly once"):
        publish_controlled(decision, plan, bundle)


def test_unknown_model_fact_slot_fails_schema_validation() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        StorytellerSelection(
            insight_id="test",
            audience=Audience.CASUAL,
            angle=Angle.TACTICAL,
            style=Style.CONCISE,
            fact_order=("invented_goal",),
        )
