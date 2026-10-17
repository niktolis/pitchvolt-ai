"""Agent role instructions remain stable, explicit, and offline-testable."""
from matchpulse.agent_policies import (
    ANALYST_INSTRUCTIONS,
    EDITORIAL_INSTRUCTIONS,
    POLICY_VERSION,
    STORYTELLER_INSTRUCTIONS,
)


def test_role_policy_contracts() -> None:
    assert POLICY_VERSION == "grounded-v1"
    for policy in (ANALYST_INSTRUCTIONS, STORYTELLER_INSTRUCTIONS, EDITORIAL_INSTRUCTIONS):
        assert len(policy.strip()) > 100
    assert "Retrieve every cited event" in ANALYST_INSTRUCTIONS
    assert "Do not invent" in ANALYST_INSTRUCTIONS
    assert "SHADOW" in STORYTELLER_INSTRUCTIONS
    assert "EXACT" in STORYTELLER_INSTRUCTIONS
    assert "independently evidenced" in STORYTELLER_INSTRUCTIONS
    assert "Never override" in EDITORIAL_INSTRUCTIONS
