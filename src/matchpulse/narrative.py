"""Evidence-grounded narrative contracts and deterministic publication gate.

No LLM/provider imports; no arbitrary prose passes automatically. This module
is the foundation for the approved Analyst -> Storyteller Foundry workflow.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from matchpulse.events import MatchEvent
from matchpulse.intelligence import TacticalInsight


class Audience(StrEnum):
    CASUAL = "casual"
    ANALYST = "analyst"
    CLUB = "club"


class ClaimKind(StrEnum):
    INSIGHT_KIND = "insight_kind"
    TEAM_ID = "team_id"
    METRIC = "metric"
    EVIDENCE_EVENT = "evidence_event"


class Claim(BaseModel):
    """A precise typed claim checked against immutable deterministic evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ClaimKind
    key: str
    value: str | int | float


class NarrativeCandidate(BaseModel):
    """Structured Storyteller response; text is never unconditionally trusted."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    insight_id: str
    audience: Audience
    headline: str = Field(min_length=1, max_length=180)
    text: str = Field(min_length=1, max_length=600)
    claims: tuple[Claim, ...] = Field(min_length=1)
    evidence_event_ids: tuple[str, ...] = Field(min_length=1)


class VerifiedNarrative(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    insight_id: str
    audience: Audience
    headline: str
    text: str
    evidence_event_ids: tuple[str, ...]
    verified_claims: tuple[Claim, ...]


@dataclass(frozen=True)
class EvidenceBundle:
    insight: TacticalInsight
    events: tuple[MatchEvent, ...]

    def __post_init__(self) -> None:
        expected = self.insight.evidence_event_ids
        actual = tuple(e.event_id for e in self.events)
        if actual != expected:
            raise ValueError("Evidence must exactly match insight source IDs and order")
        if any(event.match_id != self.insight.match_id for event in self.events):
            raise ValueError("Evidence belongs to another match")
        if any(event.provenance.source != "synthetic" for event in self.events):
            raise ValueError("Narrative evidence must have accepted synthetic provenance")


class EvidenceTool(Protocol):
    """Read-only evidence lookup port; a model may only request known insight IDs."""

    def get(self, insight_id: str) -> EvidenceBundle: ...


@dataclass(frozen=True)
class InMemoryEvidenceTool:
    """Deterministic local evidence provider for the existing fixture processor."""

    lookup: Callable[[str], EvidenceBundle]

    def get(self, insight_id: str) -> EvidenceBundle:
        result = self.lookup(insight_id)
        if result.insight.insight_id != insight_id:
            raise ValueError("Evidence tool returned another insight")
        return result


class NarrativeRejection(ValueError):
    """Narrative cannot be established from the immutable factual bundle."""


def verify_claims(candidate: NarrativeCandidate, evidence: EvidenceBundle) -> tuple[Claim, ...]:
    """Verify an explicitly bounded set of machine-readable factual claims.

    This gate deliberately does NOT certify arbitrary text as true: until a
    bounded template renderer/semantic verifier is integrated, free-form model
    prose must never be published on this contract.
    """
    insight = evidence.insight
    if candidate.insight_id != insight.insight_id:
        raise NarrativeRejection("Narrative insight ID does not match evidence")
    if candidate.evidence_event_ids != insight.evidence_event_ids:
        raise NarrativeRejection("Narrative must reference the exact evidence set")

    ids = set(insight.evidence_event_ids)
    checked: set[tuple[ClaimKind, str]] = set()
    for claim in candidate.claims:
        slot = (claim.kind, claim.key)
        if slot in checked:
            raise NarrativeRejection("Duplicate factual claim")
        checked.add(slot)
        if claim.kind == ClaimKind.INSIGHT_KIND:
            if claim.key != "kind" or claim.value != insight.kind.value:
                raise NarrativeRejection("Unsupported tactical classification")
        elif claim.kind == ClaimKind.TEAM_ID:
            if claim.key != "team_id" or claim.value != insight.team_id:
                raise NarrativeRejection("Unsupported team identity")
        elif claim.kind == ClaimKind.METRIC:
            expected = insight.metrics.get(claim.key)
            if expected is None or isinstance(claim.value, str) or claim.value != expected:
                raise NarrativeRejection("Unsupported deterministic metric")
        elif claim.kind == ClaimKind.EVIDENCE_EVENT:
            if claim.key != "event_id" or claim.value not in ids:
                raise NarrativeRejection("Unsupported event reference")
        else:
            raise NarrativeRejection("Unsupported factual claim kind")

    return candidate.claims


def verify_narrative(candidate: NarrativeCandidate, evidence: EvidenceBundle) -> VerifiedNarrative:
    """Fail closed for free-form model prose even when typed facts are correct.

    Semantic narrative policy is an unresolved product requirement; a validated
    claim manifest cannot prove that an arbitrary prose sentence is accurate.
    """
    verify_claims(candidate, evidence)
    raise NarrativeRejection("Free-form narrative requires reviewed semantic verification")


def bounded_deterministic_fallback(
    evidence: EvidenceBundle, audience: Audience
) -> VerifiedNarrative:
    """Only canonical structured facts are rendered; no model pretence."""
    insight = evidence.insight
    secs = insight.metrics["transition_duration_ms"] / 1000
    actions = insight.metrics["attacking_actions"]
    if audience == Audience.CASUAL:
        text = f"{insight.team_id}: {insight.kind.value.replace('_', ' ')} after a turnover."
    elif audience == Audience.ANALYST:
        text = (
            f"{insight.team_id}: {insight.kind.value}; "
            f"turnover-to-shot {secs:.3f}s; attacking actions {actions}."
        )
    else:
        text = (
            f"{insight.team_id}: {insight.kind.value.replace('_', ' ')}; "
            f"transition {secs:.3f}s across {actions} attacking actions."
        )
    return VerifiedNarrative(
        insight_id=insight.insight_id,
        audience=audience,
        headline=insight.kind.value.replace("_", " ").title(),
        text=text,
        evidence_event_ids=insight.evidence_event_ids,
        verified_claims=(
            Claim(kind=ClaimKind.INSIGHT_KIND, key="kind", value=insight.kind.value),
            Claim(kind=ClaimKind.TEAM_ID, key="team_id", value=insight.team_id),
            Claim(
                kind=ClaimKind.METRIC, key="transition_duration_ms",
                value=insight.metrics["transition_duration_ms"],
            ),
            Claim(
                kind=ClaimKind.METRIC, key="attacking_actions",
                value=insight.metrics["attacking_actions"],
            ),
        ),
    )
