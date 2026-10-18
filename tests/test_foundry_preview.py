"""No unexpected billable requests from public application routes."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from pitchvolt import foundry_preview
from pitchvolt.api import app
from pitchvolt.narrative import Audience
from pitchvolt.narrative_stream import NarrativeUpdate


def test_preview_disabled_by_default_and_public_replay_unchanged(monkeypatch) -> None:
    monkeypatch.delenv("PITCHVOLT_FOUNDRY_PREVIEW_ENABLED", raising=False)
    monkeypatch.setenv("PITCHVOLT_FOUNDRY_PREVIEW_TOKEN", "t" * 40)
    url = "/api/matches/high_press/narratives/foundry-preview/stream"
    with TestClient(app) as client:
        before = client.get("/api/matches/high_press/timeline").json()
        assert client.get(url, headers={"X-PitchVolt-Inference-Token": "t" * 40}).status_code == 403
        assert client.get(url).status_code == 403
        assert client.get("/api/matches/high_press/timeline").json() == before


def test_preview_requires_private_token_endpoint_and_is_single_use(monkeypatch) -> None:
    token = "locally-held-preview-token-" + "x" * 32
    monkeypatch.setenv("PITCHVOLT_FOUNDRY_PREVIEW_ENABLED", "true")
    monkeypatch.setenv("PITCHVOLT_FOUNDRY_PREVIEW_TOKEN", token)
    monkeypatch.setenv(
        "PITCHVOLT_FOUNDRY_PROJECT_ENDPOINT",
        "https://example.services.ai.azure.com/api/projects/offline",
    )
    monkeypatch.setattr(foundry_preview, "_attempt_used", False)
    observed = []

    async def fake_inference(name: str, audience: Audience):
        observed.append((name, audience))
        yield NarrativeUpdate(
            insight_id="known-id", audience=audience, headline="Verified",
            text="Canonical facts", source="foundry_controlled",
            evidence_event_ids=["event-1"],
        )

    monkeypatch.setattr(foundry_preview, "_one_insight", fake_inference)
    url = "/api/matches/high_press/narratives/foundry-preview/stream"
    with TestClient(app) as client:
        assert client.get(url).status_code == 403
        assert client.get(url, headers={"X-PitchVolt-Inference-Token": "bad"}).status_code == 403
        first = client.get(url, headers={"X-PitchVolt-Inference-Token": token})
        assert first.status_code == 200
        assert first.headers["content-type"].startswith("text/event-stream")
        assert "event: narrative_update\ndata: " in first.text
        assert "\n\nevent: narrative_complete\ndata: {}\n\n" in first.text
        assert "\\\\n" not in first.text
        data_line = next(line for line in first.text.splitlines() if line.startswith("data: {") and line != "data: {}")
        assert json.loads(data_line.removeprefix("data: "))["source"] == "foundry_controlled"
        result = client.get(url, headers={"X-PitchVolt-Inference-Token": token})
        assert result.status_code == 429
    assert observed == [("high_press", Audience.ANALYST)]


def test_preview_has_no_endpoint_without_auth(monkeypatch) -> None:
    monkeypatch.setenv("PITCHVOLT_FOUNDRY_PREVIEW_ENABLED", "true")
    monkeypatch.setenv("PITCHVOLT_FOUNDRY_PREVIEW_TOKEN", "s" * 40)
    with TestClient(app) as client:
        assert client.get("/api/matches/unknown/narratives/foundry-preview/stream").status_code == 404
        assert client.get("/api/matches/high_press/narratives/foundry-preview/stream").status_code == 403
