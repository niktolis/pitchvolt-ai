"""Approved selective Analyst -> Storyteller workflow, with controlled publication.

Providers return *decisions*, never publishable text. The backend renders
approved sentence structures exclusively from canonical evidence and metrics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from pitchvolt.evidence_links import LinkedClaim
from pitchvolt.intelligence import InsightKind
from pitchvolt.narrative import (
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


class FactSlot(StrEnum):
    """Canonical fact fragments the model may reorder but never invent."""

    TEAM = "team"
    TACTIC = "tactic"
    TRANSITION = "transition"
    ACTIONS = "actions"


FACT_SLOTS = frozenset(FactSlot)


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
    fact_order: tuple[FactSlot, ...] | None = None
    authored_headline: str | None = Field(default=None, max_length=180)
    authored_text: str | None = Field(default=None, max_length=600)
    evidence_links: tuple[LinkedClaim, ...] | None = None


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
    if selection.fact_order is not None and (
        len(selection.fact_order) != len(FACT_SLOTS)
        or set(selection.fact_order) != FACT_SLOTS
    ):
        raise NarrativeRejection("Composition must use each canonical fact exactly once")
    sustained = insight.kind == InsightKind.SUSTAINED_POSSESSION
    duration_key = "sequence_duration_ms" if sustained else "transition_duration_ms"
    count_key = "passes" if sustained else "attacking_actions"
    seconds = insight.metrics[duration_key] / 1000
    count = insight.metrics[count_key]
    duration_label = "Possession sequence" if sustained else "Turnover-to-shot"
    count_label = "Passes" if sustained else "Attacking actions"
    tactic = insight.kind.value.replace("_", " ")
    team = insight.team_id
    if selection.fact_order is not None:
        # Rendering is server-owned: only ordering is model-controlled.
        fragments = {
            FactSlot.TEAM: f"Team: {team}",
            FactSlot.TACTIC: f"Tactic: {tactic}",
            FactSlot.TRANSITION: f"{duration_label}: {seconds:.3f}s",
            FactSlot.ACTIONS: f"{count_label}: {count}",
        }
        text = " · ".join(fragments[slot] for slot in selection.fact_order) + "."
    elif selection.style == Style.TECHNICAL:
        text = (
            f"{team} — {tactic}: {duration_label.lower()} "
            f"{seconds:.3f} seconds across {count} {count_label.lower()}."
        )
    elif selection.angle == Angle.TRANSITION:
        text = (
            f"{team} completed a {seconds:.3f}-second "
            f"{duration_label.lower()} with {count} {count_label.lower()} ({tactic})."
        )
    else:
        text = f"{team} produced a {tactic} sequence with {count} {count_label.lower()}."
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
                key=duration_key,
                value=insight.metrics[duration_key],
            ),
            Claim(
                kind=ClaimKind.METRIC,
                key=count_key,
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
