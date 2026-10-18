"""No model-generated free text can cross the narrative truth boundary unverified."""
import pytest

from pitchvolt.intelligence import analyze_stream
from pitchvolt.narrative import (
    Audience,
    Claim,
    ClaimKind,
    EvidenceBundle,
    NarrativeCandidate,
    NarrativeRejection,
    bounded_deterministic_fallback,
    verify_claims,
    verify_narrative,
)
from pitchvolt.scenarios import scenario


def _bundle() -> EvidenceBundle:
    match, events = scenario("high_press")
    insight = analyze_stream(match, events)[0]
    lookup = {event.event_id: event for event in events}
    return EvidenceBundle(insight, tuple(lookup[id] for id in insight.evidence_event_ids))


def _candidate(bundle: EvidenceBundle) -> NarrativeCandidate:
    insight = bundle.insight
    return NarrativeCandidate(
        insight_id=insight.insight_id,
        audience=Audience.ANALYST,
        headline="A tactical description",
        text="Unverified claims must not be published.",
        evidence_event_ids=insight.evidence_event_ids,
        claims=(
            Claim(kind=ClaimKind.INSIGHT_KIND, key="kind", value=insight.kind.value),
            Claim(kind=ClaimKind.METRIC, key="attacking_actions",
                  value=insight.metrics["attacking_actions"]),
        ),
    )


def test_typed_evidence_claims_are_validated_but_prose_is_not_automatically_verified() -> None:
    bundle = _bundle()
    candidate = _candidate(bundle)
    assert verify_claims(candidate, bundle) == candidate.claims
    with pytest.raises(NarrativeRejection, match="semantic verification"):
        verify_narrative(candidate, bundle)


def test_hallucinated_metric_fails_closed() -> None:
    bundle = _bundle()
    candidate = _candidate(bundle)
    changed = candidate.model_copy(update={
        "claims": (
            Claim(kind=ClaimKind.METRIC, key="attacking_actions", value=999),
        )
    })
    with pytest.raises(NarrativeRejection, match="metric"):
        verify_claims(changed, bundle)


def test_wrong_insight_id_and_missing_evidence_fail_closed() -> None:
    bundle = _bundle()
    candidate = _candidate(bundle)
    with pytest.raises(NarrativeRejection, match="insight ID"):
        verify_claims(candidate.model_copy(update={"insight_id": "fabricated"}), bundle)
    with pytest.raises(NarrativeRejection, match="exact evidence"):
        verify_claims(candidate.model_copy(update={"evidence_event_ids": ("fabricated",)}), bundle)


def test_untrusted_events_cannot_replace_insight_evidence() -> None:
    bundle = _bundle()
    with pytest.raises(ValueError, match="exactly match"):
        EvidenceBundle(bundle.insight, bundle.events[:-1])


@pytest.mark.parametrize("audience", list(Audience))
def test_fallback_uses_same_canonical_metrics(audience: Audience) -> None:
    bundle = _bundle()
    result = bounded_deterministic_fallback(bundle, audience)
    assert result.insight_id == bundle.insight.insight_id
    assert result.evidence_event_ids == bundle.insight.evidence_event_ids
    assert any(claim.key == "attacking_actions" and claim.value == 4
               for claim in result.verified_claims)


def test_unknown_metric_rejected() -> None:
    bundle = _bundle()
    candidate = _candidate(bundle).model_copy(update={
        "claims": (Claim(kind=ClaimKind.METRIC, key="xg", value=0.5),)
    })
    with pytest.raises(NarrativeRejection, match="metric"):
        verify_claims(candidate, bundle)
