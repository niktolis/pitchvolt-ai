"""Candidate assessment is offline and never grants permission to publish."""
import pytest
from pydantic import ValidationError

from matchpulse.intelligence import analyze_stream
from matchpulse.narrative import (
    Audience,
    Claim,
    ClaimKind,
    EvidenceBundle,
    NarrativeCandidate,
    NarrativeRejection,
    verify_narrative,
)
from matchpulse.scenarios import scenario
from matchpulse.shadow_validation import ShadowStatus, assess_candidate


def _fixture() -> tuple[EvidenceBundle, NarrativeCandidate]:
    match, events = scenario("high_press")
    insight = analyze_stream(match, events)[0]
    index = {event.event_id: event for event in events}
    bundle = EvidenceBundle(
        insight, tuple(index[event_id] for event_id in insight.evidence_event_ids)
    )
    candidate = NarrativeCandidate(
        insight_id=insight.insight_id,
        audience=Audience.ANALYST,
        headline="A promising attack",
        text="The home side dominated possession and scored three goals.",
        claims=(
            Claim(kind=ClaimKind.INSIGHT_KIND, key="kind", value=insight.kind.value),
            Claim(kind=ClaimKind.METRIC, key="attacking_actions",
                  value=insight.metrics["attacking_actions"]),
        ),
        evidence_event_ids=insight.evidence_event_ids,
    )
    return bundle, candidate


def test_valid_claim_manifest_does_not_certify_false_prose() -> None:
    bundle, candidate = _fixture()
    assessment = assess_candidate(candidate, bundle)
    assert assessment.status == ShadowStatus.UNVERIFIED_PROSE
    assert assessment.publishable is False
    assert assessment.verified_claim_count == 2
    assert assessment.evidence_event_count == len(bundle.events)
    assert "dominated" not in assessment.model_dump_json()
    with pytest.raises(NarrativeRejection, match="semantic verification"):
        verify_narrative(candidate, bundle)


@pytest.mark.parametrize("change", ["bad_metric", "bad_evidence", "bad_insight"])
def test_invalid_claim_manifests_remain_unpublishable(change: str) -> None:
    bundle, candidate = _fixture()
    if change == "bad_metric":
        candidate = candidate.model_copy(update={
            "claims": (Claim(kind=ClaimKind.METRIC, key="attacking_actions", value=999),)
        })
    elif change == "bad_evidence":
        candidate = candidate.model_copy(update={"evidence_event_ids": ("fake",)})
    else:
        candidate = candidate.model_copy(update={"insight_id": "fabricated"})
    result = assess_candidate(candidate, bundle)
    assert result.status == ShadowStatus.INVALID_CLAIMS
    assert result.publishable is False
    assert result.verified_claim_count == 0


def test_assessment_cannot_be_marked_publishable() -> None:
    from matchpulse.shadow_validation import ShadowAssessment

    with pytest.raises(ValidationError):
        ShadowAssessment(
            status=ShadowStatus.UNVERIFIED_PROSE,
            insight_id="sample",
            verified_claim_count=2,
            evidence_event_count=4,
            publishable=True,
        )
