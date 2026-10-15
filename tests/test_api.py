"""Contract tests for repeatable one-way streaming and evidence access."""
from fastapi.testclient import TestClient

from matchpulse.api import app, timeline

client = TestClient(app)


def test_scenarios_health_and_state():
    assert client.get("/health").json() == {"status": "ok"}
    assert "high_press" in client.get("/api/scenarios").json()["scenarios"]
    state = client.get("/api/matches/high_press/state").json()
    assert state["insights"][0]["kind"] == "high_press"


def test_stream_ids_and_evidence():
    messages = timeline("high_press")
    assert [m.id for m in messages] == list(range(1, len(messages) + 1))
    response = client.get("/api/matches/high_press/stream?speed=1000")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    ids = [int(line.removeprefix("id: ")) for line in response.text.splitlines()
           if line.startswith("id: ")]
    assert ids == list(range(1, len(messages) + 1))
    insight = next(m for m in messages if m.kind == "tactical_insight")
    result = client.get(
        f"/api/matches/high_press/evidence/{insight.payload['insight_id']}"
    )
    assert result.status_code == 200
    assert {e["event_id"] for e in result.json()["events"]} == set(
        insight.payload["evidence_event_ids"]
    )


def test_reconnect_resume_and_stateless_replay():
    messages = timeline("counterattack")
    entire = client.get("/api/matches/counterattack/stream?speed=1000").text
    resumed = client.get("/api/matches/counterattack/stream?speed=1000",
                         headers={"Last-Event-ID": "2"}).text
    assert "id: 1\n" in entire
    assert "id: 1\n" not in resumed
    assert "id: 3\n" in resumed
    assert len(messages) >= 3
    assert entire == client.get("/api/matches/counterattack/stream?speed=1000").text


def test_error_boundaries():
    assert client.get("/api/matches/unknown/state").status_code == 404
    assert client.get("/api/matches/high_press/stream?speed=0").status_code == 422
    assert client.get("/api/matches/high_press/stream",
                      headers={"Last-Event-ID": "not-an-int"}).status_code == 400
    assert client.get("/api/matches/high_press/stream?after=999").status_code == 400
    assert client.get("/api/matches/high_press/evidence/missing").status_code == 404
