import pytest
from pydantic import ValidationError

from matchpulse.events import EventType, MatchEvent, Point, Provenance, validate_stream
from matchpulse.simulation import MATCH, high_press_replay


def test_deterministic_replay() -> None:
    a = high_press_replay(42)
    assert [e.model_dump(mode="json") for e in a] == [
        e.model_dump(mode="json") for e in high_press_replay(42)
    ]
    assert [e.event_type for e in a] == [
        EventType.PRESSURE, EventType.PASS, EventType.TURNOVER,
        EventType.CARRY, EventType.PASS, EventType.SHOT,
    ]
    assert high_press_replay(43) != a


def test_json_roundtrip() -> None:
    event = high_press_replay()[0]
    assert MatchEvent.model_validate_json(event.model_dump_json()) == event


def test_invalid_pass_destination() -> None:
    payload = high_press_replay()[1].model_dump()
    payload["destination"] = None
    with pytest.raises(ValidationError, match="requires a destination"):
        MatchEvent.model_validate(payload)


def test_invalid_coordinates() -> None:
    with pytest.raises(ValidationError):
        Point(x=106, y=0)


def test_non_synthetic_source_rejected() -> None:
    with pytest.raises(ValidationError, match="synthetic"):
        Provenance(generator="x", generator_version="1", seed=0, scenario="x", source="real")


def test_duplicate_event_id_rejected() -> None:
    events = high_press_replay()
    events[1] = events[1].model_copy(update={"event_id": events[0].event_id})
    with pytest.raises(ValueError, match="Duplicate"):
        validate_stream(events, MATCH)


def test_invalid_possession_team_rejected() -> None:
    events = high_press_replay()
    events[0] = events[0].model_copy(update={"possession_team_id": "unknown"})
    with pytest.raises(ValueError, match="Unknown"):
        validate_stream(events, MATCH)
