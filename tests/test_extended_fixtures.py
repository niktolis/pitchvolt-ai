"""Baseline invariants for deterministic, explicitly uncalibrated replay."""
from fastapi.testclient import TestClient

from matchpulse.api import app
from matchpulse.events import EventType, Outcome, validate_stream
from matchpulse.intelligence import InsightKind, analyze_stream
from matchpulse.scenarios import scenario
from matchpulse.statsbomb_reference import (
    REFERENCE_ACTION_COUNTS,
    REFERENCE_PROJECTED_COUNT,
    calibrated_action_quotas,
)


def test_long_fixture_is_deterministic_across_requests():
    match, events = scenario("extended_match", 42)
    same_match, same_events = scenario("extended_match", 42)
    assert match == same_match
    assert [e.model_dump_json() for e in events] == [e.model_dump_json() for e in same_events]
    assert len(events) == 220
    assert events[0].clock_ms == 0
    assert events[-1].clock_ms == 5_400_000
    assert events[-1].period == 2
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
    assert all(e.evidence["fixture"] == "statsbomb_reference_weighted_actions" for e in events)


def test_api_timeline_and_catalog_include_long_fixture():
    client = TestClient(app)
    assert "extended_match" in client.get("/api/scenarios").json()["scenarios"]
    response = client.get("/api/matches/extended_match/timeline")
    assert response.status_code == 200
    items = response.json()
    assert sum(item["kind"] == "match_event" for item in items) == 220
    assert items[0]["payload"]["period"] == 1
    assert items[-1]["payload"]["period"] == 2


def test_action_family_quota_matches_pinned_reference() -> None:
    from collections import Counter

    quotas = calibrated_action_quotas(216)
    assert sum(quotas.values()) == 216
    assert sum(REFERENCE_ACTION_COUNTS.values()) == REFERENCE_PROJECTED_COUNT
    _, events = scenario("extended_match", 42)
    types = Counter(e.event_type for e in events)
    assert types[EventType.TURNOVER] == 4
    assert types[EventType.GOAL] == 1
    # Four scripted insight windows need four shots, against a three-shot corpus ratio.
    assert types[EventType.SHOT] + types[EventType.GOAL] == max(4, quotas[EventType.SHOT])
    assert types[EventType.CARRY] == quotas[EventType.CARRY] - max(0, 4 - quotas[EventType.SHOT])
    for kind in (EventType.PASS, EventType.PRESSURE):
        assert types[kind] == quotas[kind]



def test_scripted_high_press_inside_larger_match_is_evidence_backed() -> None:
    match, events = scenario("extended_match", 42)
    insights = analyze_stream(match, events)
    assert len(insights) == 4
    assert all(item.kind == InsightKind.HIGH_PRESS for item in insights)
    insight = next(item for item in insights if item.evidence_event_ids[0] == events[70].event_id)
    window = events[70:78]
    assert len(window) == 8
    assert events[73].event_type == EventType.PASS
    assert events[73].outcome == Outcome.FAILURE
    assert events[73].evidence["under_pressure"] is True
    assert events[74].event_type == EventType.TURNOVER
    assert events[77].event_type == EventType.GOAL
    assert insight.evidence_event_ids == tuple(event.event_id for event in window)
    assert insight.metrics["transition_duration_ms"] == 7_500
    assert insight.metrics["attacking_actions"] == 4
    assert all(e.evidence["scripted_tactical_window"] for e in window)


def test_multiple_grounded_insights_distributed_across_halves() -> None:
    match, events = scenario("extended_match", 42)
    insights = analyze_stream(match, events)
    expected_windows = (31, 71, 151, 191)
    assert len(insights) == len(expected_windows)
    for insight, start in zip(insights, expected_windows, strict=True):
        window = events[start - 1:start + 7]
        assert insight.evidence_event_ids == tuple(e.event_id for e in window)
        assert insight.metrics["transition_duration_ms"] == 7_500
        assert insight.metrics["attacking_actions"] == 4
        assert all(e.evidence["scripted_tactical_window"] for e in window)
    assert {i.period for i in insights} == {1, 2}


def test_offline_extended_smoke_scenario_without_inference(capsys) -> None:
    import asyncio

    from matchpulse import foundry_smoke

    assert asyncio.run(foundry_smoke.run(["--scenario", "extended_match"])) == 0
    output = capsys.readouterr().out
    assert '"scenario": "extended_match"' in output
    assert "No Azure credentials loaded" in output
    bundle = foundry_smoke.fixture("extended_match")
    assert bundle.insight.kind == InsightKind.HIGH_PRESS
    assert len(bundle.events) == 8
