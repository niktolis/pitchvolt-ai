"""Offline claim-to-text linkage for original Storyteller shadow prose.

A span and its machine-readable claim can be checked deterministically, but
the surrounding prose may still contain unsupported claims. This module NEVER
authorizes publication and performs no model inference.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from pitchvolt.narrative import (
    Claim,
    EvidenceBundle,
    NarrativeCandidate,
    NarrativeRejection,
    verify_claims,
)


class LinkedClaim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    claim: Claim
    excerpt: str = Field(min_length=1, max_length=240)
    evidence_event_ids: tuple[str, ...] = Field(min_length=1)


class LinkStatus(StrEnum):
    LINKED_SHADOW = "linked_shadow_not_semantically_verified"
    INVALID_CLAIMS = "invalid_claims"
    MISSING_SPAN = "missing_span"
    INVALID_EVIDENCE_LINK = "invalid_evidence_link"
    INCOMPLETE_COVERAGE = "incomplete_claim_coverage"


@dataclass(frozen=True)
class LinkAssessment:
    status: LinkStatus
    linked_claim_count: int
    publishable: bool = False


def assess_evidence_links(
    candidate: NarrativeCandidate,
    bundle: EvidenceBundle,
    links: tuple[LinkedClaim, ...],
) -> LinkAssessment:
    """Check provenance, claim correspondence and exact excerpt presence.

    This deliberately does NOT establish that a prose assertion entails the
    cited evidence. Passing links are useful for review and future evaluation,
    never direct publication authorization.
    """
    try:
        verified = verify_claims(candidate, bundle)
    except NarrativeRejection:
        return LinkAssessment(LinkStatus.INVALID_CLAIMS, 0)
    expected = set(bundle.insight.evidence_event_ids)
    if not links or len(links) != len(verified) or {l.claim for l in links} != set(verified):
        return LinkAssessment(LinkStatus.INCOMPLETE_COVERAGE, 0)
    content = candidate.headline + "\n" + candidate.text
    for link in links:
        if link.excerpt not in content:
            return LinkAssessment(LinkStatus.MISSING_SPAN, 0)
        if not set(link.evidence_event_ids).issubset(expected):
            return LinkAssessment(LinkStatus.INVALID_EVIDENCE_LINK, 0)
    return LinkAssessment(LinkStatus.LINKED_SHADOW, len(links))
