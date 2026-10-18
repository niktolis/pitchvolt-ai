"""Measured event-type reference from an actual pinned StatsBomb Open Data match.

Numbers are a SOURCE EVENT CENSUS, not synthetic player/team data.
The file itself is not redistributed. Do not infer turnovers or scores from
these aggregate event types.
"""
from __future__ import annotations

from pitchvolt.events import EventType

REFERENCE_MATCH_ID = "9880"
REFERENCE_COMMIT = "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"
REFERENCE_SHA256 = "515986eb6fc6084d3559860ab23ee47c9999c1ad476aa5fd35f693115519e4e8"
REFERENCE_SOURCE_URL = (
    f"https://github.com/hudl/open-data/blob/{REFERENCE_COMMIT}/data/events/{REFERENCE_MATCH_ID}.json"
)
REFERENCE_LINEUP_SHA256 = "f2c95764e4c7ad724954cc08263ae667a82e0abe2197737565613932878bf749"
REFERENCE_TEAM_IDS = (207, 217)
REFERENCE_REFERENCED_PLAYERS = 28
REFERENCE_SUBSTITUTION_COUNT = 6
REFERENCE_GOAL_COUNT = 3
REFERENCE_GOAL_COUNTS_BY_TEAM = {207: 1, 217: 2}
REFERENCE_SOURCE_COUNT = 3947
REFERENCE_PROJECTED_COUNT = 2379

# Original source event counts, before any fictional possession additions.
REFERENCE_ACTION_COUNTS = {
    EventType.PASS: 1162,
    EventType.CARRY: 890,
    EventType.PRESSURE: 298,
    EventType.SHOT: 29,
}


def calibrated_action_quotas(total: int) -> dict[EventType, int]:
    """Allocate exact integer action counts using stable largest remainders.

    This calibrates only broad action frequencies against one historical match;
    it does not make temporal, team or goal probability distributions realistic.
    """
    if total < 1:
        raise ValueError("Action count must be positive")
    source_total = sum(REFERENCE_ACTION_COUNTS.values())
    if source_total != REFERENCE_PROJECTED_COUNT:
        raise RuntimeError("Reference action census is inconsistent")
    quotas = {
        kind: (count * total) // source_total
        for kind, count in REFERENCE_ACTION_COUNTS.items()
    }
    to_allocate = total - sum(quotas.values())
    ranked = sorted(
        REFERENCE_ACTION_COUNTS,
        key=lambda kind: (
            -((REFERENCE_ACTION_COUNTS[kind] * total) % source_total),
            kind.value,
        ),
    )
    for kind in ranked[:to_allocate]:
        quotas[kind] += 1
    return quotas
