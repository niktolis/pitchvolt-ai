"""Approved selective Analyst -> Storyteller workflow, with controlled publication.

Providers return *decisions*, never publishable text. The backend renders
approved sentence structures exclusively from canonical evidence and metrics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from matchpulse.narrative import (
    Audience,
    Claim,
    ClaimKind,
    EvidenceBundle,
    EvidenceTool,
    NarrativeRejection,
    VerifiedNarrative,
    bounded_deterministic_fallback,
)


class Angle(StrEnum):
    TRANSITION = "transition"
    TACTICAL = "tactical"


class Style(StrEnum):
    CONCISE = "concise"
    TECHNICAL = "technical"


class AnalystPlan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    insight_id: str
    angle: Angle
    evidence_event_ids: tuple[str, ...]


class StorytellerSelection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    insight_id: str
    audience: Audience
    angle: Angle
    style: Style


class Analyst(Protocol):
    async def analyze(self, evidence: EvidenceBundle) -> AnalystPlan: ...


class Storyteller(Protocol):
    async def select(
        self, plan: AnalystPlan, evidence: EvidenceBundle, audience: Audience
    ) -> StorytellerSelection: ...


@dataclass(frozen=True)
class TraceStep:
    role: str
    action: str
    duration_ms: float
    reference: str | None = None


@dataclass(frozen=True)
class NarrativeResult:
    narrative: VerifiedNarrative
    source: str  # "controlled" or "fallback", never "foundry" without real provider
    trace: tuple[TraceStep, ...]
    rejection_reason: str | None = None


def publish_controlled(
    selection: StorytellerSelection, plan: AnalystPlan, bundle: EvidenceBundle
) -> VerifiedNarrative:
    """Render verified prose from server-owned templates, not LLM text."""
    insight = bundle.insight
    if selection.insight_id != insight.insight_id or plan.insight_id != insight.insight_id:
        raise NarrativeRejection("Stale or mismatched insight ID")
    if selection.angle != plan.angle:
        raise NarrativeRejection("Storyteller changed the validated Analyst angle")
    if plan.evidence_event_ids != insight.evidence_event_ids:
        raise NarrativeRejection("Analyst failed to cite exact evidence")
    if selection.angle not in Angle or selection.style not in Style:
        raise NarrativeRejection("Unsupported narrative selection")
    seconds = insight.metrics["transition_duration_ms"] / 1000
    count = insight.metrics["attacking_actions"]
    tactic = insight.kind.value.replace("_", " ")
    team = insight.team_id
    if selection.style == Style.TECHNICAL:
        text = (
            f"{team} — {tactic}: turnover-to-shot transition "
            f"{seconds:.3f} seconds across {count} attacking actions."
        )
    elif selection.angle == Angle.TRANSITION:
        text = (
            f"{team} completed a {seconds:.3f}-second transition "
            f"with {count} attacking actions ({tactic})."
        )
    else:
        text = f"{team} produced a {tactic} sequence with {count} attacking actions."
    return VerifiedNarrative(
        insight_id=insight.insight_id,
        audience=selection.audience,
        headline=f"{tactic.title()} · {team}",
        text=text,
        evidence_event_ids=insight.evidence_event_ids,
        verified_claims=(
            Claim(kind=ClaimKind.INSIGHT_KIND, key="kind", value=insight.kind.value),
            Claim(kind=ClaimKind.TEAM_ID, key="team_id", value=team),
            Claim(
                kind=ClaimKind.METRIC,
                key="transition_duration_ms",
                value=insight.metrics["transition_duration_ms"],
            ),
            Claim(
                kind=ClaimKind.METRIC,
                key="attacking_actions",
                value=count,
            ),
        ),
    )


@dataclass
class Orchestrator:
    evidence_tool: EvidenceTool
    analyst: Analyst
    storyteller: Storyteller

    async def narrate(self, insight_id: str, audience: Audience) -> NarrativeResult:
        trace: list[TraceStep] = []
        start = perf_counter()
        bundle = self.evidence_tool.get(insight_id)
        trace.append(TraceStep("evidence", "lookup", (perf_counter() - start) * 1000))
        try:
            # Independently resolve cited evidence through the read-only port.
            # This is a real local tool invocation, not a model-initiated call.
            for event_id in bundle.insight.evidence_event_ids:
                start = perf_counter()
                event = self.evidence_tool.get_event(insight_id, event_id)
                if event.event_id != event_id or event.match_id != bundle.insight.match_id:
                    raise NarrativeRejection("Evidence tool returned a mismatched event")
                trace.append(
                    TraceStep("evidence", "get_event", (perf_counter() - start) * 1000, event_id)
                )
            start = perf_counter()
            plan = await self.analyst.analyze(bundle)
            trace.append(TraceStep("analyst", "plan", (perf_counter() - start) * 1000))
            if plan.insight_id != insight_id or plan.evidence_event_ids != bundle.insight.evidence_event_ids:
                raise NarrativeRejection("Analyst supplied mismatched evidence")
            start = perf_counter()
            decision = await self.storyteller.select(plan, bundle, audience)
            trace.append(
                TraceStep("storyteller", "select", (perf_counter() - start) * 1000)
            )
            if decision.audience != audience:
                raise NarrativeRejection("Storyteller changed requested audience")
            start = perf_counter()
            narrative = publish_controlled(decision, plan, bundle)
            trace.append(TraceStep("verifier", "publish", (perf_counter() - start) * 1000))
            return NarrativeResult(narrative, "controlled", tuple(trace))
        except (NarrativeRejection, ValueError, TimeoutError) as exc:
            trace.append(TraceStep("verifier", "reject", 0))
            return NarrativeResult(
                bounded_deterministic_fallback(bundle, audience),
                "fallback",
                tuple(trace),
                str(exc),
            )
