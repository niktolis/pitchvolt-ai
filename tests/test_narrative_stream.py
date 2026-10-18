"""Independent narrative stream must not mutate/reorder event publication."""
import asyncio
import json

from fastapi.testclient import TestClient

from pitchvolt.api import app, timeline
from pitchvolt.narrative import Audience
from pitchvolt.narrative_stream import narrative_updates

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
    assert data["verification"] == "controlled"
    assert [step["role"] for step in data["trace"][-3:]] == [
        "analyst", "storyteller", "verifier",
    ]
    assert all(step["duration_ms"] >= 0 for step in data["trace"])
    assert all(step["action"] != "reject" for step in data["trace"])
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
    from pitchvolt import narrative_stream

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
    assert payload["verification"] == "deterministic_fallback"
    assert payload["trace"][-1]["action"] == "reject"
    assert "Local agent unavailable" not in response.text
    assert payload["evidence_event_ids"]
    assert "event: narrative_complete" in response.text


def test_role_timeout_falls_back_without_failing_sse(monkeypatch) -> None:
    from pitchvolt import narrative_stream

    async def timeout(awaitable, **kwargs):
        # The mocked wait_for never schedules its coroutine; close it to
        # preserve asyncio ownership and avoid an unawaited-coroutine warning.
        awaitable.close()
        raise TimeoutError("Model timed out")

    monkeypatch.setattr(narrative_stream.asyncio, "wait_for", timeout)
    response = client.get("/api/matches/high_press/narratives/stream")
    assert response.status_code == 200
    assert '"source":"deterministic_fallback"' in response.text
    assert '"verification":"deterministic_fallback"' in response.text
    assert "event: narrative_complete" in response.text


def test_provider_selection_defaults_to_local(monkeypatch) -> None:
    from pitchvolt import narrative_stream
    monkeypatch.delenv("PITCHVOLT_NARRATIVE_PROVIDER", raising=False)
    analyst, storyteller, source = narrative_stream._provider_roles()
    assert isinstance(analyst, narrative_stream.LocalAnalyst)
    assert isinstance(storyteller, narrative_stream.LocalStoryteller)
    assert source == "local_controlled"


def test_foundry_mode_remains_blocked_even_with_valid_settings(monkeypatch) -> None:
    monkeypatch.setenv("PITCHVOLT_NARRATIVE_PROVIDER", "foundry")
    monkeypatch.setenv(
        "PITCHVOLT_FOUNDRY_PROJECT_ENDPOINT",
        "https://example.services.ai.azure.com/api/projects/sample",
    )
    monkeypatch.setenv("PITCHVOLT_FOUNDRY_MODEL", "not-deployed")
    response = client.get("/api/matches/high_press/narratives/stream")
    assert response.status_code == 200
    assert '"source":"deterministic_fallback"' in response.text
    assert "event: narrative_complete" in response.text


def test_unknown_narrative_provider_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("PITCHVOLT_NARRATIVE_PROVIDER", "unexpected")
    response = client.get("/api/matches/high_press/narratives/stream")
    assert response.status_code == 200
    assert '"source":"deterministic_fallback"' in response.text
    assert "event: narrative_complete" in response.text
