"""Role boundaries and all audience flavors are source-controlled contracts."""
import pytest

from matchpulse.agent_policies import (
    ANALYST_INSTRUCTIONS,
    AUDIENCE_POLICIES,
    CORE_POLICY,
    EDITORIAL_INSTRUCTIONS,
    POLICY_VERSION,
    STORYTELLER_INSTRUCTIONS,
    audience_instruction,
)
from matchpulse.narrative import Audience


def test_role_policy_contracts() -> None:
    assert POLICY_VERSION == "broadcast-shadow-v1"
    for policy in (ANALYST_INSTRUCTIONS, STORYTELLER_INSTRUCTIONS, EDITORIAL_INSTRUCTIONS):
        assert len(policy.strip()) > 400
        assert CORE_POLICY in policy
        assert "structured" in policy
        assert "synthetic" in policy
    assert "Retrieve every cited event" in ANALYST_INSTRUCTIONS
    assert "Do not invent" in ANALYST_INSTRUCTIONS
    assert "SHADOW" in STORYTELLER_INSTRUCTIONS
    assert "verbatim" in STORYTELLER_INSTRUCTIONS
    assert "null or a permutation" in STORYTELLER_INSTRUCTIONS
    assert "a subset is invalid" in STORYTELLER_INSTRUCTIONS
    assert "never override" in EDITORIAL_INSTRUCTIONS.lower()


def test_each_audience_has_distinct_editorial_flavor() -> None:
    assert set(AUDIENCE_POLICIES) == set(Audience)
    instructions = [audience_instruction(audience) for audience in Audience]
    assert len(set(instructions)) == len(Audience)
    for audience, policy in AUDIENCE_POLICIES.items():
        assert policy.audience == audience
        assert audience.value in policy.instruction()
        assert len(policy.instruction()) > 200
        assert "Editorial constraints" in policy.instruction()


def test_audience_policies_do_not_override_common_grounding() -> None:
    for audience in Audience:
        text = audience_instruction(audience)
        assert "No player names" in text or "player intent" in text or "player names" in text
        assert "Audience:" in text


def test_unknown_audience_fails_closed() -> None:
    with pytest.raises(KeyError):
        audience_instruction("broadcast_unreviewed")  # type: ignore[arg-type]


def test_live_broadcast_voice_keeps_evidence_constraints() -> None:
    casual = audience_instruction(Audience.CASUAL)
    analyst = audience_instruction(Audience.ANALYST)
    club = audience_instruction(Audience.CLUB)
    assert "Passionate live Premier League-style play-by-play" in casual
    assert "spontaneous" in casual
    assert "tactical precision" in analyst
    assert "club-studio pundit" in club
    assert "SHADOW" in STORYTELLER_INSTRUCTIONS
    assert "never\ninvent a goal" in STORYTELLER_INSTRUCTIONS
    assert "Never imply a fictional match" in CORE_POLICY
