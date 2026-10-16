"""Separate bounded narrative SSE; never delays the football-event fast path."""
from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from matchpulse.events import MatchEvent, MatchMetadata
from matchpulse.foundry_adapter import FoundryConfig, FoundryDisabled, FoundryRoles
from matchpulse.intelligence import TacticalInsight, analyze_stream
from matchpulse.narrative import (
    Audience,
    EvidenceBundle,
    InMemoryEvidenceTool,
    bounded_deterministic_fallback,
)
from matchpulse.scenarios import SCENARIO_NAMES, scenario
from matchpulse.workflow import (
    AnalystPlan,
    Angle,
    Orchestrator,
    StorytellerSelection,
    Style,
)

router = APIRouter()


class NarrativeUpdate(BaseModel):
    insight_id: str
    audience: Audience
    headline: str
    text: str
    source: str
    evidence_event_ids: list[str]


class LocalAnalyst:
    """Deterministic role implementation; not an AI model or Foundry agent."""

    async def analyze(self, bundle: EvidenceBundle) -> AnalystPlan:
        await asyncio.sleep(0)
        return AnalystPlan(
            insight_id=bundle.insight.insight_id,
            angle=Angle.TACTICAL,
            evidence_event_ids=bundle.insight.evidence_event_ids,
        )


class LocalStoryteller:
    """Choose only permitted style; backend owns actual prose."""

    async def select(
        self, plan: AnalystPlan, bundle: EvidenceBundle, audience: Audience
    ) -> StorytellerSelection:
        await asyncio.sleep(0)
        return StorytellerSelection(
            insight_id=plan.insight_id,
            audience=audience,
            angle=plan.angle,
            style=Style.TECHNICAL if audience == Audience.ANALYST else Style.CONCISE,
        )


def _bundles(match: MatchMetadata, events: list[MatchEvent]) -> dict[str, EvidenceBundle]:
    insight_list: list[TacticalInsight] = analyze_stream(match, events)
    event_index = {event.event_id: event for event in events}
    return {
        insight.insight_id: EvidenceBundle(
            insight, tuple(event_index[event_id] for event_id in insight.evidence_event_ids)
        )
        for insight in insight_list
    }


def _provider_roles() -> tuple[object, object, str]:
    """Resolve roles without granting permission for paid inference."""
    provider = os.environ.get("MATCHPULSE_NARRATIVE_PROVIDER", "local").strip().lower()
    if provider == "local":
        return LocalAnalyst(), LocalStoryteller(), "local_controlled"
    if provider == "foundry":
        config = FoundryConfig(
            project_endpoint=os.environ.get("MATCHPULSE_FOUNDRY_PROJECT_ENDPOINT", ""),
            model_deployment=os.environ.get("MATCHPULSE_FOUNDRY_MODEL", ""),
            inference_explicitly_approved=False,
        )
        roles = FoundryRoles(config)
        return roles, roles, "foundry_controlled"
    raise ValueError(f"Unsupported narrative provider: {provider}")


async def narrative_updates(name: str, audience: Audience) -> AsyncIterator[NarrativeUpdate]:
    """Fail-closed role selection; fallback never calls a remote provider."""
    match, events = scenario(name)
    bundles = _bundles(match, events)
    if not bundles:
        return
    tool = InMemoryEvidenceTool(lambda insight_id: bundles[insight_id])
    try:
        analyst, storyteller, controlled_source = _provider_roles()
    except (FoundryDisabled, ValueError):
        analyst, storyteller, controlled_source = None, None, "deterministic_fallback"
    orchestrator = (
        Orchestrator(tool, analyst, storyteller)
        if analyst is not None and storyteller is not None
        else None
    )
    for insight_id in bundles:
        try:
            # A slow or failing role must never break finite SSE completion.
            # Cancellation of a disconnected client is intentionally not swallowed.
            if orchestrator is None:
                raise FoundryDisabled("Provider is not approved or configured")
            result = await asyncio.wait_for(orchestrator.narrate(insight_id, audience), timeout=2)
            narrative = result.narrative
            source = (
                controlled_source
                if result.source == "controlled"
                else "deterministic_fallback"
            )
        except (TimeoutError, RuntimeError, ValueError):
            # No LLM-generated text survives this branch. The trusted
            # immutable evidence bundle is our only publication input.
            narrative = bounded_deterministic_fallback(bundles[insight_id], audience)
            source = "deterministic_fallback"
        yield NarrativeUpdate(
            insight_id=narrative.insight_id,
            audience=narrative.audience,
            headline=narrative.headline,
            text=narrative.text,
            source=source,
            evidence_event_ids=list(narrative.evidence_event_ids),
        )


@router.get("/api/matches/{name}/narratives/stream", include_in_schema=False)
async def narrative_stream(
    name: str,
    audience: Audience = Audience.CASUAL,
    delay_ms: int = Query(default=0, ge=0, le=5000),
) -> StreamingResponse:
    if name not in SCENARIO_NAMES:
        raise HTTPException(status_code=404, detail="Unknown scenario")

    async def publish() -> AsyncIterator[str]:
        async for update in narrative_updates(name, audience):
            if delay_ms:
                await asyncio.sleep(delay_ms / 1000)
            yield f"event: narrative_update\ndata: {update.model_dump_json()}\n\n"
        yield "event: narrative_complete\ndata: {}\n\n"

    return StreamingResponse(
        publish(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
