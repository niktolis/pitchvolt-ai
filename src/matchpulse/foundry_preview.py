"""Manual, local-only, single-use Foundry narrative SSE integration.

This route is never enabled by selecting a provider alone. A private process
token and explicit server opt-in are required. The ordinary replay and narrative
routes stay deterministic and public.
"""
from __future__ import annotations

import asyncio
import os
import secrets
from collections.abc import AsyncIterator

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from matchpulse.foundry_adapter import FoundryConfig, FoundryRoles, RoleSettings
from matchpulse.foundry_smoke import (
    ANALYST_DEPLOYMENT, SMOKE_ANALYST_OUTPUT_TOKENS, STORYTELLER_DEPLOYMENT,
    create_smoke_project_client,
)
from matchpulse.narrative import Audience, InMemoryEvidenceTool, bounded_deterministic_fallback
from matchpulse.narrative_stream import NarrativeUpdate, _bundles
from matchpulse.scenarios import SCENARIO_NAMES, scenario
from matchpulse.workflow import Orchestrator

router = APIRouter()
_attempt_lock = asyncio.Lock()
_attempt_used = False


async def _one_insight(name: str, audience: Audience) -> AsyncIterator[NarrativeUpdate]:
    """At most one insight and one two-role attempt; no autonomous retries."""
    from azure.identity.aio import AzureCliCredential

    match, events = scenario(name)
    bundles = _bundles(match, events)
    if not bundles:
        return
    insight_id, bundle = next(iter(bundles.items()))
    credential = AzureCliCredential()
    project_client = None
    try:
        config = FoundryConfig(
            project_endpoint=os.environ["MATCHPULSE_FOUNDRY_PROJECT_ENDPOINT"],
            model_deployment=ANALYST_DEPLOYMENT,
            storyteller_model_deployment=STORYTELLER_DEPLOYMENT,
            inference_explicitly_approved=True,
            max_tool_calls_per_analyst=min(12, len(bundle.events)),
            timeout_seconds_per_role=15.0,
            analyst_settings=RoleSettings(max_output_tokens=SMOKE_ANALYST_OUTPUT_TOKENS),
        )
        project_client = create_smoke_project_client(config.project_endpoint, credential)
        roles = FoundryRoles(config, credential=credential, project_client=project_client)
        tool = InMemoryEvidenceTool(lambda _: bundle)
        result = await asyncio.wait_for(
            Orchestrator(tool, roles, roles).narrate(insight_id, audience),
            timeout=35.0,
        )
        narrative = result.narrative
        source = "foundry_controlled" if result.source == "controlled" else "deterministic_fallback"
    except Exception:  # noqa: BLE001 - public stream must never leak provider exceptions
        narrative = bounded_deterministic_fallback(bundle, audience)
        source = "deterministic_fallback"
    finally:
        if project_client is not None:
            await project_client.close()
        await credential.close()
    yield NarrativeUpdate(
        insight_id=narrative.insight_id,
        audience=narrative.audience,
        headline=narrative.headline,
        text=narrative.text,
        source=source,
        evidence_event_ids=list(narrative.evidence_event_ids),
    )


@router.get("/api/matches/{name}/narratives/foundry-preview/stream", include_in_schema=False)
async def foundry_preview_stream(
    name: str,
    request: Request,
    audience: Audience = Audience.ANALYST,
    inference_token: str | None = Header(default=None, alias="X-MatchPulse-Inference-Token"),
) -> StreamingResponse:
    """One locally initiated, operator-authorized attempt per process lifetime."""
    if name not in SCENARIO_NAMES:
        raise HTTPException(status_code=404, detail="Unknown scenario")
    configured_token = os.environ.get("MATCHPULSE_FOUNDRY_PREVIEW_TOKEN", "")
    if (
        os.environ.get("MATCHPULSE_FOUNDRY_PREVIEW_ENABLED") != "true"
        or request.client is None
        or request.client.host not in ("127.0.0.1", "::1", "testclient")
        or len(configured_token) < 32
        or inference_token is None
        or not secrets.compare_digest(inference_token, configured_token)
    ):
        raise HTTPException(status_code=403, detail="Foundry preview is not authorized")
    if not os.environ.get("MATCHPULSE_FOUNDRY_PROJECT_ENDPOINT"):
        raise HTTPException(status_code=503, detail="Foundry project is not configured")
    global _attempt_used
    async with _attempt_lock:
        if _attempt_used:
            raise HTTPException(status_code=429, detail="Preview attempt already consumed")
        _attempt_used = True

    async def publish() -> AsyncIterator[str]:
        try:
            async for update in _one_insight(name, audience):
                yield f"event: narrative_update\\ndata: {update.model_dump_json()}\\n\\n"
        except Exception:  # noqa: BLE001 - protect SSE completion on unexpected failure
            yield "event: narrative_error\\ndata: {}\\n\\n"
        yield "event: narrative_complete\\ndata: {}\\n\\n"

    return StreamingResponse(
        publish(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
