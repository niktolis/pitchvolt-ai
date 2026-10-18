"""Deliberately narrow, offline-only publication eligibility for model-authored text.

This is NOT a general semantic verifier. Only exact canonical sentences from
an explicit finite grammar qualify; any additional phrase fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pitchvolt.narrative import (
    EvidenceBundle,
    NarrativeCandidate,
    NarrativeRejection,
    VerifiedNarrative,
    verify_claims,
)


class GroundingStatus(StrEnum):
    ELIGIBLE = "eligible_bounded_grammar"
    INVALID_CLAIMS = "invalid_claims"
    UNRECOGNIZED_PROSE = "unrecognized_prose"


@dataclass(frozen=True)
class GroundingResult:
    status: GroundingStatus
    matched_grammar: str | None
    eligible: bool


def approved_phrasings(bundle: EvidenceBundle) -> tuple[tuple[str, str, str], ...]:
    """All permitted variants are composed solely from the canonical insight."""
    insight = bundle.insight
    team = insight.team_id
    tactic = insight.kind.value.replace("_", " ")
    actions = insight.metrics["attacking_actions"]
    seconds = insight.metrics["transition_duration_ms"] / 1000
    headline = f"{team} {tactic} sequence"
    return (
        (
            "transition_first",
            headline,
            (f"{team} completed a {seconds:g}-second turnover-to-shot transition "
             f"following a {tactic} sequence with {actions} attacking actions."),
        ),
        (
            "actions_first",
            headline,
            (f"{team} produced {actions} attacking actions in a {tactic} sequence, "
             f"with {seconds:g} seconds from turnover to shot."),
        ),
    )


def assess_grounded_prose(candidate: NarrativeCandidate, bundle: EvidenceBundle) -> GroundingResult:
    """Exact matching eliminates unknown assertions, not merely manifest errors."""
    try:
        verify_claims(candidate, bundle)
    except NarrativeRejection:
        return GroundingResult(GroundingStatus.INVALID_CLAIMS, None, False)
    for grammar, headline, text in approved_phrasings(bundle):
        if candidate.headline == headline and candidate.text == text:
            return GroundingResult(GroundingStatus.ELIGIBLE, grammar, True)
    return GroundingResult(GroundingStatus.UNRECOGNIZED_PROSE, None, False)


def publish_eligible_candidate(
    candidate: NarrativeCandidate, bundle: EvidenceBundle
) -> VerifiedNarrative:
    """For isolated local preview only; public SSE still uses controlled renderer."""
    outcome = assess_grounded_prose(candidate, bundle)
    if not outcome.eligible:
        raise NarrativeRejection("Model prose is outside the reviewed bounded grammar")
    return VerifiedNarrative(
        insight_id=candidate.insight_id,
        audience=candidate.audience,
        headline=candidate.headline,
        text=candidate.text,
        evidence_event_ids=candidate.evidence_event_ids,
        verified_claims=candidate.claims,
    )
