"""Independent narrative stream must not mutate/reorder event publication."""
import asyncio
import json

from fastapi.testclient import TestClient

from matchpulse.api import app, timeline
from matchpulse.narrative import Audience
from matchpulse.narrative_stream import narrative_updates

client = TestClient(app)


def test_narrative_stream_uses_same_insight_and_exact_evidence() -> None:
    insight = next(m.payload for m in timeline("high_press") if m.kind == "tactical_insight")
    response = client.get("/api/matches/high_press/narratives/stream?audience=analyst")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: narrative_update" in response.text
    assert response.text.endswith("event: narrative_complete\ndata: {}\n\n")
    payloads = [
        json.loads(line[6:]) for line in response.text.splitlines()
        if line.startswith("data: ") and line != "data: {}"
    ]
    assert len(payloads) == 1
    data = payloads[0]
    assert data["insight_id"] == insight.insight_id
    assert data["audience"] == "analyst"
    assert data["source"] == "local_controlled"
    assert data["evidence_event_ids"] == insight.evidence_event_ids
    assert str(insight.metrics["attacking_actions"]) in data["text"]
    assert "event: match_event" not in response.text


def test_narratives_are_disabled_for_unknown_scenarios() -> None:
    assert client.get("/api/matches/missing/narratives/stream").status_code == 404
    assert client.get("/api/matches/high_press/narratives/stream?audience=other").status_code == 422
    assert client.get("/api/matches/high_press/narratives/stream?delay_ms=5001").status_code == 422


def test_narrative_negative_control_emits_no_false_insights() -> None:
    response = client.get("/api/matches/sustained_possession/narratives/stream")
    assert "event: narrative_update" not in response.text
    assert "event: narrative_complete" in response.text


def test_narrative_requests_leave_original_replay_byte_identical() -> None:
    before = client.get("/api/matches/high_press/stream?speed=1000").text
    narrative = client.get("/api/matches/high_press/narratives/stream").text
    assert "event: narrative_update" in narrative
    after = client.get("/api/matches/high_press/stream?speed=1000").text
    assert before == after


def test_local_narrative_uses_no_remote_provider_and_keeps_audience() -> None:
    async def collect():
        return [u async for u in narrative_updates("counterattack", Audience.CLUB)]
    updates = asyncio.run(collect())
    assert len(updates) == 1
    assert updates[0].audience == Audience.CLUB
    assert updates[0].source == "local_controlled"


def test_provider_failure_returns_evidence_backed_fallback(monkeypatch) -> None:
    from matchpulse import narrative_stream

    async def fail(self, evidence):
        raise RuntimeError("Local agent unavailable")

    monkeypatch.setattr(narrative_stream.LocalAnalyst, "analyze", fail)
    response = client.get("/api/matches/high_press/narratives/stream?audience=analyst")
    assert response.status_code == 200
    payload = next(
        json.loads(line[6:])
        for line in response.text.splitlines()
        if line.startswith("data: ") and line != "data: {}"
    )
    assert payload["source"] == "deterministic_fallback"
    assert payload["evidence_event_ids"]
    assert "event: narrative_complete" in response.text


def test_role_timeout_falls_back_without_failing_sse(monkeypatch) -> None:
    from matchpulse import narrative_stream

    async def timeout(*args, **kwargs):
        raise TimeoutError("Model timed out")

    monkeypatch.setattr(narrative_stream.asyncio, "wait_for", timeout)
    response = client.get("/api/matches/high_press/narratives/stream")
    assert response.status_code == 200
    assert '"source":"deterministic_fallback"' in response.text
    assert "event: narrative_complete" in response.text
