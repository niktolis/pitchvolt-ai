"""Deterministic, fictional high-press tactical scenario.

This is a deliberately bounded demonstration fixture, not a full-match simulator.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from random import Random

from matchpulse.events import (
    EventType,
    MatchEvent,
    MatchMetadata,
    Outcome,
    Point,
    Provenance,
    validate_stream,
)

MATCH = MatchMetadata(match_id="synthetic-press-001", home_team_id="harbor-fc", away_team_id="ridge-fc")
START = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
VERSION = "0.1.0"


def high_press_replay(seed: int = 42) -> list[MatchEvent]:
    """Generate the same causal sequence on every replay for a given seed."""
    rng = Random(seed)
    jitter = [rng.randint(0, 2) for _ in range(6)]
    provenance = Provenance(
        generator="matchpulse-high-press",
        generator_version=VERSION,
        seed=seed,
        scenario="high-press-to-shot",
    )

    # Pressure → pressured pass → turnover → carry → dangerous pass → shot.
    descriptions = [
        (EventType.PRESSURE, "harbor-fc", "harbor-9", Outcome.SUCCESS, (78, 28), None, "ridge-fc", {}),
        (EventType.PASS, "ridge-fc", "ridge-4", Outcome.FAILURE, (76, 30), (70, 34), "ridge-fc", {"under_pressure": True}),
        (EventType.TURNOVER, "harbor-fc", "harbor-8", Outcome.SUCCESS, (70, 34), None, "harbor-fc", {"forced": True}),
        (EventType.CARRY, "harbor-fc", "harbor-8", Outcome.SUCCESS, (70, 34), (86, 31), "harbor-fc", {}),
        (EventType.PASS, "harbor-fc", "harbor-8", Outcome.SUCCESS, (86, 31), (96, 35), "harbor-fc", {"line_breaking": True}),
        (EventType.SHOT, "harbor-fc", "harbor-9", Outcome.FAILURE, (96, 35), (105, 34), "harbor-fc", {"on_target": True}),
    ]
    output: list[MatchEvent] = []
    for i, (kind, team, player, outcome, pos, dest, possession, evidence) in enumerate(descriptions):
        clock_ms = 67 * 60_000 + (20 + i * 3 + jitter[i]) * 1000
        output.append(
            MatchEvent(
                match_id=MATCH.match_id,
                event_id=f"{MATCH.match_id}-e{i + 1:03d}",
                sequence=i + 1,
                period=2,
                clock_ms=clock_ms,
                observed_at=START + timedelta(milliseconds=clock_ms),
                team_id=team,
                player_id=player,
                event_type=kind,
                outcome=outcome,
                location=Point(x=pos[0], y=pos[1]),
                destination=Point(x=dest[0], y=dest[1]) if dest else None,
                possession_team_id=possession,
                evidence=evidence,
                provenance=provenance,
            )
        )
    validate_stream(output, MATCH)
    return output
