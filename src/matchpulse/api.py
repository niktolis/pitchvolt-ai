"""Replayable HTTP/SSE adapter for the deterministic football domain.

Stateless, per-request replay sessions avoid shared mutable match state across viewers.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from matchpulse.intelligence import MatchProcessor, analyze_stream
from matchpulse.scenarios import scenario

app = FastAPI(title="MatchPulse AI", version="0.2.0")
SCENARIOS = ("high_press", "counterattack", "sustained_possession")


class ReplayMessage(BaseModel):
    id: int
    kind: str
    match_id: str
    payload: dict


def _load(name: str):
    if name not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Unknown scenario")
    return scenario(name)


def timeline(name: str) -> list[ReplayMessage]:
    """Single deterministic publication contract for replay and catch-up."""
    match, events = _load(name)
    processor = MatchProcessor(match)
    messages: list[ReplayMessage] = []
    for event in events:
        insights = processor.ingest(event)
        messages.append(ReplayMessage(
            id=len(messages) + 1, kind="match_event", match_id=match.match_id,
            payload=event.model_dump(mode="json"),
        ))
        for insight in insights:
            messages.append(ReplayMessage(
                id=len(messages) + 1, kind="tactical_insight", match_id=match.match_id,
                payload={
                    "insight_id": insight.insight_id,
                    "kind": insight.kind.value,
                    "team_id": insight.team_id,
                    "clock_ms": insight.clock_ms,
                    "evidence_event_ids": list(insight.evidence_event_ids),
                    "metrics": insight.metrics,
                },
            ))
    return messages


def _sse(message: ReplayMessage) -> str:
    return f"id: {message.id}\nevent: {message.kind}\ndata: {message.model_dump_json()}\n\n"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/scenarios")
def list_scenarios() -> dict[str, list[str]]:
    return {"scenarios": list(SCENARIOS)}


@app.get("/api/matches/{name}/state")
def match_state(name: str) -> dict:
    match, events = _load(name)
    return {
        "match": match.model_dump(),
        "events_processed": len(events),
        "possession_team_id": events[-1].possession_team_id if events else None,
        "insights": [
            {
                "insight_id": i.insight_id, "kind": i.kind.value,
                "evidence_event_ids": list(i.evidence_event_ids), "metrics": i.metrics,
            }
            for i in analyze_stream(match, events)
        ],
    }


@app.get("/api/matches/{name}/evidence/{insight_id:path}")
def evidence(name: str, insight_id: str) -> dict:
    match, events = _load(name)
    insights = analyze_stream(match, events)
    insight = next((i for i in insights if i.insight_id == insight_id), None)
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    ids = set(insight.evidence_event_ids)
    return {
        "insight_id": insight.insight_id,
        "events": [e.model_dump(mode="json") for e in events if e.event_id in ids],
        "metrics": insight.metrics,
    }


@app.get("/api/matches/{name}/stream")
async def stream(
    name: str,
    speed: Annotated[float, Query(ge=0.1, le=1000)] = 1.0,
    after: Annotated[int, Query(ge=0)] = 0,
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    messages = timeline(name)
    if last_event_id is not None:
        try:
            cursor = int(last_event_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid Last-Event-ID") from exc
    else:
        cursor = after
    if cursor < 0 or cursor > len(messages):
        raise HTTPException(status_code=400, detail="Replay cursor out of range")

    async def publish() -> AsyncIterator[str]:
        _, events = _load(name)
        clocks = {e.event_id: e.clock_ms for e in events}
        previous_clock: int | None = None
        for message in messages:
            if message.kind == "match_event":
                clock = clocks[message.payload["event_id"]]
            else:
                clock = int(message.payload["clock_ms"])
            if message.id <= cursor:
                previous_clock = clock
                continue
            if previous_clock is not None:
                delay = max(0.0, (clock - previous_clock) / 1000 / speed)
                if delay:
                    await asyncio.sleep(delay)
            yield _sse(message)
            previous_clock = clock
        yield "event: replay_complete\ndata: {}\n\n"

    return StreamingResponse(publish(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
