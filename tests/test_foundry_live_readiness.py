"""No Azure access required: simulate SDK envelopes and shadow publication boundary."""
from types import SimpleNamespace

import pytest

from pitchvolt.foundry_adapter import sanitized_response_metadata, usage_counts
from pitchvolt.intelligence import analyze_stream
from pitchvolt.narrative import Audience, EvidenceBundle
from pitchvolt.scenarios import scenario
from pitchvolt.workflow import (
    AnalystPlan,
    Angle,
    FactSlot,
    StorytellerSelection,
    Style,
    publish_controlled,
)


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (SimpleNamespace(usage=SimpleNamespace(input_tokens=12, output_tokens=7)), (12, 7)),
        (SimpleNamespace(usage={"prompt_tokens": 13, "completion_tokens": 6}), (13, 6)),
        (SimpleNamespace(messages=[SimpleNamespace(usage={"input_tokens": 5, "output_tokens": 2})]), (5, 2)),
        (SimpleNamespace(usage=SimpleNamespace(input_tokens=True, output_tokens=-2)), (None, None)),
        (SimpleNamespace(messages=[SimpleNamespace(content="secret")]), (None, None)),
    ],
)
def test_usage_telemetry_is_optional_and_allowlisted(response, expected) -> None:
    assert usage_counts(response) == expected
    serialized = str(sanitized_response_metadata(response))
    assert "secret" not in serialized


def test_authored_storyteller_fields_do_not_change_trusted_renderer() -> None:
    match, events = scenario("high_press")
    insight = analyze_stream(match, events)[0]
    index = {event.event_id: event for event in events}
    bundle = EvidenceBundle(
        insight, tuple(index[event_id] for event_id in insight.evidence_event_ids)
    )
    plan = AnalystPlan(
        insight_id=insight.insight_id, angle=Angle.TACTICAL,
        evidence_event_ids=insight.evidence_event_ids,
    )
    selection = StorytellerSelection(
        insight_id=insight.insight_id,
        audience=Audience.ANALYST,
        angle=Angle.TACTICAL,
        style=Style.TECHNICAL,
        fact_order=tuple(FactSlot),
        authored_headline="Invented 4-0 result",
        authored_text="There were twelve goals and 100 percent possession.",
    )
    result = publish_controlled(selection, plan, bundle)
    assert "twelve goals" not in result.text
    assert "4-0" not in result.headline
    assert str(insight.metrics["attacking_actions"]) in result.text
