"""Evidence links are useful provenance metadata, never publication authority."""
from matchpulse.evidence_links import LinkStatus, LinkedClaim, assess_evidence_links
from matchpulse.foundry_smoke import fixture
from matchpulse.narrative import Audience, Claim, ClaimKind, NarrativeCandidate


def test_original_text_can_be_linked_in_shadow_without_publication() -> None:
    bundle = fixture()
    insight = bundle.insight
    claims = (
        Claim(kind=ClaimKind.TEAM_ID, key="team_id", value=insight.team_id),
        Claim(kind=ClaimKind.METRIC, key="attacking_actions", value=insight.metrics["attacking_actions"]),
    )
    candidate = NarrativeCandidate(
        insight_id=insight.insight_id,
        audience=Audience.ANALYST,
        headline="Pressing and the breakthrough",
        text="harbor-fc registered 4 attacking actions, a sequence worth examining.",
        claims=claims,
        evidence_event_ids=insight.evidence_event_ids,
    )
    links = (
        LinkedClaim(claim=claims[0], excerpt="harbor-fc", evidence_event_ids=(insight.evidence_event_ids[0],)),
        LinkedClaim(claim=claims[1], excerpt="4 attacking actions", evidence_event_ids=(insight.evidence_event_ids[1],)),
    )
    result = assess_evidence_links(candidate, bundle, links)
    assert result.status == LinkStatus.LINKED_SHADOW
    assert result.linked_claim_count == 2
    assert result.publishable is False


def test_links_reject_unmatched_text_and_non_evidence_events() -> None:
    bundle = fixture()
    insight = bundle.insight
    claim = Claim(kind=ClaimKind.TEAM_ID, key="team_id", value=insight.team_id)
    candidate = NarrativeCandidate(
        insight_id=insight.insight_id, audience=Audience.CASUAL,
        headline="Pressing", text="harbor-fc acted quickly.",
        claims=(claim,), evidence_event_ids=insight.evidence_event_ids,
    )
    missing = (LinkedClaim(claim=claim, excerpt="something absent", evidence_event_ids=(insight.evidence_event_ids[0],)),)
    assert assess_evidence_links(candidate, bundle, missing).status == LinkStatus.MISSING_SPAN
    external = (LinkedClaim(claim=claim, excerpt="harbor-fc", evidence_event_ids=("invented",)),)
    assert assess_evidence_links(candidate, bundle, external).status == LinkStatus.INVALID_EVIDENCE_LINK
    assert assess_evidence_links(candidate, bundle, ()).status == LinkStatus.INCOMPLETE_COVERAGE


def test_provenance_links_do_not_certify_unrelated_prose() -> None:
    bundle = fixture()
    insight = bundle.insight
    claim = Claim(kind=ClaimKind.TEAM_ID, key="team_id", value=insight.team_id)
    candidate = NarrativeCandidate(
        insight_id=insight.insight_id, audience=Audience.CLUB,
        headline="Dominant win", text="harbor-fc completely dominated and won 5-0.",
        claims=(claim,), evidence_event_ids=insight.evidence_event_ids,
    )
    links = (LinkedClaim(claim=claim, excerpt="harbor-fc", evidence_event_ids=(insight.evidence_event_ids[0],)),)
    result = assess_evidence_links(candidate, bundle, links)
    assert result.publishable is False
