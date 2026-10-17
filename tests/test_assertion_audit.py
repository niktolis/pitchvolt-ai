"""Offline assertion audit must abstain on unconstrained free prose."""
import pytest

from matchpulse.assertion_audit import AssertionStatus, audit_assertions
from matchpulse.foundry_smoke import fixture
from matchpulse.narrative import Audience, Claim, ClaimKind, NarrativeCandidate


@pytest.mark.parametrize(
    ("headline", "text", "expected"),
    [
        ("Sequence", "4 attacking actions and 9 seconds.", (AssertionStatus.SUPPORTED, AssertionStatus.SUPPORTED)),
        ("Sequence", "7 attacking actions and 11 seconds.", (AssertionStatus.CONTRADICTED, AssertionStatus.CONTRADICTED)),
        ("Dominant victory", "harbor-fc won 5-0 thanks to its striker.", (AssertionStatus.UNVERIFIABLE,)),
        ("Sequence", "harbor-fc played with superior intensity.", (AssertionStatus.UNVERIFIABLE,)),
    ],
)
def test_adversarial_assertion_audit_abstains(
    headline: str, text: str, expected: tuple[AssertionStatus, ...]
) -> None:
    bundle = fixture()
    candidate = NarrativeCandidate(
        insight_id=bundle.insight.insight_id,
        audience=Audience.ANALYST,
        headline=headline,
        text=text,
        evidence_event_ids=bundle.insight.evidence_event_ids,
        claims=(Claim(kind=ClaimKind.TEAM_ID, key="team_id", value=bundle.insight.team_id),),
    )
    audit = audit_assertions(candidate, bundle)
    statuses = tuple(finding.status for finding in audit.findings)
    for status in expected:
        assert status in statuses
    assert audit.complete_coverage is False
    assert audit.publishable is False


def test_metric_citation_does_not_make_fabricated_outcome_publishable() -> None:
    bundle = fixture()
    candidate = NarrativeCandidate(
        insight_id=bundle.insight.insight_id,
        audience=Audience.CASUAL,
        headline="A sensational victory",
        text="harbor-fc completed 4 attacking actions in 9 seconds and won 6-0.",
        evidence_event_ids=bundle.insight.evidence_event_ids,
        claims=(
            Claim(kind=ClaimKind.METRIC, key="attacking_actions", value=4),
            Claim(kind=ClaimKind.METRIC, key="transition_duration_ms", value=9000),
        ),
    )
    audit = audit_assertions(candidate, bundle)
    assert any(f.status == AssertionStatus.SUPPORTED for f in audit.findings)
    assert any(f.status == AssertionStatus.UNVERIFIABLE for f in audit.findings)
    assert audit.complete_coverage is False
    assert audit.publishable is False
