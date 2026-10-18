"""Offline shadow assessment of proposed model prose; never a publication decision."""
from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from pitchvolt.narrative import (
    EvidenceBundle,
    NarrativeCandidate,
    NarrativeRejection,
    verify_claims,
)


class ShadowStatus(StrEnum):
    INVALID_CLAIMS = "invalid_claims"
    UNVERIFIED_PROSE = "unverified_prose"


class ShadowAssessment(BaseModel):
    """Audit only: no proposed text or raw provider error is retained."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: ShadowStatus
    insight_id: str
    verified_claim_count: int
    evidence_event_count: int
    publishable: Literal[False] = False


def assess_candidate(candidate: NarrativeCandidate, evidence: EvidenceBundle) -> ShadowAssessment:
    """Check machine-readable claims without certifying arbitrary natural language.

    Even perfectly matching claim manifests do not establish that the headline
    or prose contains no additional unsupported football assertions.
    """
    try:
        checked = verify_claims(candidate, evidence)
    except NarrativeRejection:
        return ShadowAssessment(
            status=ShadowStatus.INVALID_CLAIMS,
            insight_id=evidence.insight.insight_id,
            verified_claim_count=0,
            evidence_event_count=len(evidence.events),
        )
    return ShadowAssessment(
        status=ShadowStatus.UNVERIFIED_PROSE,
        insight_id=evidence.insight.insight_id,
        verified_claim_count=len(checked),
        evidence_event_count=len(evidence.events),
    )
