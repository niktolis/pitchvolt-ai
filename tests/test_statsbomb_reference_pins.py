"""Pin real historical source fixture measurements without redistributing files."""
from matchpulse.statsbomb_reference import (
    REFERENCE_GOAL_COUNT,
    REFERENCE_GOAL_COUNTS_BY_TEAM,
    REFERENCE_LINEUP_SHA256,
    REFERENCE_REFERENCED_PLAYERS,
    REFERENCE_SUBSTITUTION_COUNT,
    REFERENCE_TEAM_IDS,
)


def test_reference_bundle_audit_measurements_are_internally_consistent():
    assert len(REFERENCE_LINEUP_SHA256) == 64
    assert all(digit in "0123456789abcdef" for digit in REFERENCE_LINEUP_SHA256)
    assert REFERENCE_TEAM_IDS == tuple(sorted(REFERENCE_TEAM_IDS))
    assert set(REFERENCE_GOAL_COUNTS_BY_TEAM) == set(REFERENCE_TEAM_IDS)
    assert sum(REFERENCE_GOAL_COUNTS_BY_TEAM.values()) == REFERENCE_GOAL_COUNT
    assert REFERENCE_GOAL_COUNT == 3
    assert REFERENCE_SUBSTITUTION_COUNT == 6
    assert REFERENCE_REFERENCED_PLAYERS == 28
