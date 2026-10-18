import pytest

from pitchvolt.events import EventType
from pitchvolt.intelligence import InsightKind, MatchProcessor, analyze_stream
from pitchvolt.scenarios import scenario


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("high_press", InsightKind.HIGH_PRESS),
        ("counterattack", InsightKind.COUNTERATTACK),
        ("sustained_possession", None),
    ],
)
def test_scenario_deterministic_insights(name: str, expected: InsightKind | None) -> None:
    match, events = scenario(name)
    insights = analyze_stream(match, events)
    assert [insight.kind for insight in insights] == ([] if expected is None else [expected])
    assert events == scenario(name)[1]
    if insights:
        assert set(insights[0].evidence_event_ids).issubset({e.event_id for e in events})
        assert insights[0].metrics["transition_duration_ms"] >= 0


def test_stream_batch_equivalence() -> None:
    match, events = scenario("high_press")
    processor = MatchProcessor(match)
    published = [insight for e in events for insight in processor.ingest(e)]
    assert published == analyze_stream(match, events)


def test_reject_duplicate_sequence_without_state_change() -> None:
    match, events = scenario("counterattack")
    processor = MatchProcessor(match)
    processor.ingest(events[0])
    with pytest.raises(ValueError, match="sequence"):
        processor.ingest(events[0])
    assert len(processor.events) == 1


def test_reject_implicit_possession_switch() -> None:
    match, events = scenario("counterattack")
    processor = MatchProcessor(match)
    processor.ingest(events[0])
    invalid = events[1].model_copy(update={"event_type": EventType.CARRY})
    with pytest.raises(ValueError, match="explicit turnover"):
        processor.ingest(invalid)
    assert len(processor.events) == 1
