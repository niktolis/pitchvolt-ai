"""Bounded grammar: assertions absent from the evidence never pass publication."""
import pytest

from matchpulse.foundry_smoke import fixture
from matchpulse.grounded_prose import (
    GroundingStatus,
    approved_phrasings,
    assess_grounded_prose,
    publish_eligible_candidate,
)
from matchpulse.narrative import (
    Audience,
    Claim,
    ClaimKind,
    NarrativeCandidate,
    NarrativeRejection,
)


def candidate(headline: str, text: str) -> NarrativeCandidate:
    bundle = fixture()
    insight = bundle.insight
    return NarrativeCandidate(
        insight_id=insight.insight_id, audience=Audience.ANALYST,
        headline=headline, text=text,
        claims=(
            Claim(kind=ClaimKind.INSIGHT_KIND, key="kind", value=insight.kind.value),
            Claim(kind=ClaimKind.TEAM_ID, key="team_id", value=insight.team_id),
            Claim(kind=ClaimKind.METRIC, key="transition_duration_ms",
                  value=insight.metrics["transition_duration_ms"]),
            Claim(kind=ClaimKind.METRIC, key="attacking_actions",
                  value=insight.metrics["attacking_actions"]),
        ),
        evidence_event_ids=insight.evidence_event_ids,
    )


@pytest.mark.parametrize("variant", [0, 1])
def test_exact_approved_phrasing_is_eligible(variant: int) -> None:
    bundle = fixture()
    _, headline, text = approved_phrasings(bundle)[variant]
    original = candidate(headline, text)
    outcome = assess_grounded_prose(original, bundle)
    assert outcome.eligible
    assert outcome.status == GroundingStatus.ELIGIBLE
    published = publish_eligible_candidate(original, bundle)
    assert published.text == text
    assert published.verified_claims == original.claims


@pytest.mark.parametrize("extra", [
    " Harbor FC dominated the opposition.",
    " The score was 4-0.",
    " They maintained constant pressure throughout the match.",
    " Their possession was superior.",
    " The striker scored.",
    " A spectacular tactical edge.",
    " They created five shots.",
])
def test_unknown_claims_are_not_eligible(extra: str) -> None:
    bundle = fixture()
    _, headline, text = approved_phrasings(bundle)[0]
    proposed = candidate(headline, text + extra)
    outcome = assess_grounded_prose(proposed, bundle)
    assert outcome.status == GroundingStatus.UNRECOGNIZED_PROSE
    assert not outcome.eligible
    with pytest.raises(NarrativeRejection, match="bounded grammar"):
        publish_eligible_candidate(proposed, bundle)


def test_valid_manifest_does_not_prove_arbitrary_prose() -> None:
    bundle = fixture()
    proposed = candidate("Harbor FC dominates", "Harbor FC was completely superior.")
    assert not assess_grounded_prose(proposed, bundle).eligible


def test_wrong_claims_fail_even_when_words_match() -> None:
    bundle = fixture()
    _, headline, text = approved_phrasings(bundle)[1]
    original = candidate(headline, text)
    wrong = original.model_copy(update={
        "claims": (Claim(kind=ClaimKind.METRIC, key="attacking_actions", value=77),)
    })
    assert assess_grounded_prose(wrong, bundle).status == GroundingStatus.INVALID_CLAIMS


def test_one_character_changed_disqualifies_prose() -> None:
    bundle = fixture()
    _, headline, text = approved_phrasings(bundle)[0]
    assert not assess_grounded_prose(candidate(headline, text.replace("9-second", "8-second")), bundle).eligible
