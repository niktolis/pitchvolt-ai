"""Baseline invariants for deterministic, explicitly uncalibrated replay."""
from fastapi.testclient import TestClient

from matchpulse.api import app
from matchpulse.events import EventType, validate_stream
from matchpulse.scenarios import scenario


def test_long_fixture_is_deterministic_across_requests():
    match, events = scenario("extended_match", 42)
    same_match, same_events = scenario("extended_match", 42)
    assert match == same_match
    assert [e.model_dump_json() for e in events] == [e.model_dump_json() for e in same_events]
    assert len(events) == 220
    assert {e.period for e in events} == {1, 2}
    assert all(e.provenance.source == "synthetic" for e in events)
    validate_stream(events, match)


def test_different_seed_produces_distinct_fixture_without_changing_event_count():
    _, first = scenario("extended_match", 42)
    _, second = scenario("extended_match", 43)
    assert len(first) == len(second)
    assert first[50].location != second[50].location


def test_source_backed_goals_and_no_implicit_score():
    _, events = scenario("extended_match", 42)
    goals = [e for e in events if e.event_type == EventType.GOAL]
    assert goals
    assert all(e.outcome.value == "success" and e.destination is not None for e in goals)
    assert all(e.evidence["fixture"] == "seeded_uncalibrated" for e in events)


def test_api_timeline_and_catalog_include_long_fixture():
    client = TestClient(app)
    assert "extended_match" in client.get("/api/scenarios").json()["scenarios"]
    response = client.get("/api/matches/extended_match/timeline")
    assert response.status_code == 200
    items = response.json()
    assert sum(item["kind"] == "match_event" for item in items) == 220
    assert items[0]["payload"]["period"] == 1
    assert items[-1]["payload"]["period"] == 2
