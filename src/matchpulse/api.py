"""Replayable HTTP/SSE adapter for the deterministic football domain.

Stateless, per-request replay sessions avoid shared mutable match state across viewers.
The adapter owns transport DTOs; football validation and detection remain in MatchProcessor.
"""
from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from matchpulse.events import MatchEvent, MatchMetadata
from matchpulse.foundry_preview import router as foundry_preview_router
from matchpulse.intelligence import MatchProcessor, TacticalInsight, analyze_stream
from matchpulse.narrative_stream import router as narrative_router
from matchpulse.scenarios import SCENARIO_NAMES, scenario

app = FastAPI(title="MatchPulse AI", version="0.3.0")
app.include_router(narrative_router)
app.include_router(foundry_preview_router)


class TacticalInsightPayload(BaseModel):
    insight_id: str
    kind: str
    team_id: str
    clock_ms: int
    evidence_event_ids: list[str]
    metrics: dict[str, int | float]


class ReplayMessage(BaseModel):
    id: int
    kind: Literal["match_event", "tactical_insight"]
    match_id: str
    payload: MatchEvent | TacticalInsightPayload


class ScenarioCatalog(BaseModel):
    scenarios: list[str]


class MatchStateResponse(BaseModel):
    match: MatchMetadata
    events_processed: int
    possession_team_id: str | None
    insights: list[TacticalInsightPayload]


class EvidenceResponse(BaseModel):
    insight_id: str
    events: list[MatchEvent]
    metrics: dict[str, int | float]


def _insight_payload(insight: TacticalInsight) -> TacticalInsightPayload:
    """One transport mapping for every API surface that exposes an insight."""
    return TacticalInsightPayload(
        insight_id=insight.insight_id,
        kind=insight.kind.value,
        team_id=insight.team_id,
        clock_ms=insight.clock_ms,
        evidence_event_ids=list(insight.evidence_event_ids),
        metrics=insight.metrics,
    )


def _load(name: str) -> tuple[MatchMetadata, list[MatchEvent]]:
    if name not in SCENARIO_NAMES:
        raise HTTPException(status_code=404, detail="Unknown scenario")
    return scenario(name)


def timeline(name: str) -> list[ReplayMessage]:
    """Single deterministic publication contract for replay, UI and catch-up."""
    match, events = _load(name)
    processor = MatchProcessor(match)
    messages: list[ReplayMessage] = []
    for event in events:
        insights = processor.ingest(event)
        messages.append(
            ReplayMessage(
                id=len(messages) + 1,
                kind="match_event",
                match_id=match.match_id,
                payload=event,
            )
        )
        for insight in insights:
            messages.append(
                ReplayMessage(
                    id=len(messages) + 1,
                    kind="tactical_insight",
                    match_id=match.match_id,
                    payload=_insight_payload(insight),
                )
            )
    return messages


def _sse(message: ReplayMessage) -> str:
    return (
        f"id: {message.id}\n"
        f"event: {message.kind}\n"
        f"data: {message.model_dump_json()}\n\n"
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/scenarios", response_model=ScenarioCatalog)
def list_scenarios() -> ScenarioCatalog:
    return ScenarioCatalog(scenarios=list(SCENARIO_NAMES))


@app.get("/api/matches/{name}/timeline", response_model=list[ReplayMessage])
def replay_timeline(name: str) -> list[ReplayMessage]:
    """Finite deterministic snapshot used for contract generation and replay inspection."""
    return timeline(name)


@app.get("/api/matches/{name}/state", response_model=MatchStateResponse)
def match_state(name: str) -> MatchStateResponse:
    match, events = _load(name)
    return MatchStateResponse(
        match=match,
        events_processed=len(events),
        possession_team_id=events[-1].possession_team_id if events else None,
        insights=[_insight_payload(item) for item in analyze_stream(match, events)],
    )


@app.get("/api/matches/{name}/evidence/{insight_id:path}", response_model=EvidenceResponse)
def evidence(name: str, insight_id: str) -> EvidenceResponse:
    match, events = _load(name)
    insights = analyze_stream(match, events)
    insight = next((item for item in insights if item.insight_id == insight_id), None)
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    ids = set(insight.evidence_event_ids)
    return EvidenceResponse(
        insight_id=insight.insight_id,
        events=[event for event in events if event.event_id in ids],
        metrics=insight.metrics,
    )


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
        previous_clock: int | None = None
        for message in messages:
            clock = message.payload.clock_ms
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

    return StreamingResponse(
        publish(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


_web_dist = Path(os.environ.get("MATCHPULSE_WEB_DIST", "web/dist"))
if _web_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_web_dist), html=True), name="matchpulse-web")
