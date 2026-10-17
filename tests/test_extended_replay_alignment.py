"""End-to-end replay contract: four insights, SSE, evidence and cursor IDs."""

import json

from fastapi.testclient import TestClient

from matchpulse.api import app, timeline
from matchpulse.intelligence import analyze_stream
from matchpulse.scenarios import scenario


def test_extended_timeline_and_evidence_match_detector() -> None:
    match, events = scenario("extended_match")
    actual = analyze_stream(match, events)
    published = timeline("extended_match")
    insights = [message.payload for message in published if message.kind == "tactical_insight"]

    assert len(insights) == len(actual) == 4
    assert [i.insight_id for i in insights] == [i.insight_id for i in actual]
    assert [i.clock_ms for i in insights] == [i.clock_ms for i in actual]
    assert len({i.insight_id for i in insights}) == 4
    assert [message.id for message in published] == list(range(1, len(published) + 1))
    assert len([message for message in published if message.kind == "match_event"]) == 220

    canonical_events = {event.event_id: event for event in events}
    client = TestClient(app)
    for insight in insights:
        response = client.get(
            f"/api/matches/extended_match/evidence/{insight.insight_id}"
        )
        assert response.status_code == 200
        evidence = response.json()
        assert evidence["insight_id"] == insight.insight_id
        assert evidence["metrics"] == insight.metrics
        assert [event["event_id"] for event in evidence["events"]] == insight.evidence_event_ids
        assert all(
            event["clock_ms"] <= insight.clock_ms
            and event["event_id"] in canonical_events
            and event["player_id"] == canonical_events[event["event_id"]].player_id
            for event in evidence["events"]
        )


def test_extended_sse_resume_is_identical_to_replay_snapshot() -> None:
    client = TestClient(app)
    snapshot = client.get("/api/matches/extended_match/timeline").json()
    cursor = len(snapshot) - 3
    response = client.get(
        "/api/matches/extended_match/stream",
        params={"speed": 1000, "after": cursor},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    seen_ids = [
        int(line.removeprefix("id: "))
        for line in response.text.splitlines()
        if line.startswith("id: ")
    ]
    actual = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ") and line != "data: {}"
    ]
    assert seen_ids == [item["id"] for item in snapshot[cursor:]]
    assert actual == snapshot[cursor:]
    assert "event: replay_complete" in response.text

    # Header-based reconnect supersedes a conflicting query cursor.
    resumed = client.get(
        "/api/matches/extended_match/stream",
        params={"speed": 1000, "after": 0},
        headers={"Last-Event-ID": str(len(snapshot) - 1)},
    )
    remaining = [
        json.loads(line.removeprefix("data: "))
        for line in resumed.text.splitlines()
        if line.startswith("data: ") and line != "data: {}"
    ]
    assert remaining == snapshot[-1:]
