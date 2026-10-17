"""Repeatable two-half football-like replay fixtures for navigation testing.

These sequences are fictional test data, not StatsBomb observations or a
statistically calibrated football simulator. Source calibration is a separate
acceptance criterion of issue #65.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from random import Random

from matchpulse.events import EventType, MatchEvent, MatchMetadata, Outcome, Point, Provenance, validate_stream
from matchpulse.simulation import MATCH

EXTENDED_SCENARIO = "extended_match"
EVENTS_PER_HALF = 110
HALF_DURATION_MS = 2_700_000


def extended_match(seed: int = 42) -> tuple[MatchMetadata, list[MatchEvent]]:
    rng = Random(seed)
    match = MATCH.model_copy(update={"match_id": f"synthetic-extended-match-{seed}"})
    provenance = Provenance(
        generator="matchpulse-extended-fixture",
        generator_version="0.1.0",
        seed=seed,
        scenario=EXTENDED_SCENARIO,
    )
    start = datetime(2026, 1, 1, tzinfo=UTC)
    teams = (match.home_team_id, match.away_team_id)
    events: list[MatchEvent] = []
    for half in (1, 2):
        for position in range(EVENTS_PER_HALF):
            index = len(events) + 1
            # Include sparse time windows and two stable halves. Every event is
            # grounded in the synthetic generation seed and absolute match clock.
            offset = (position * HALF_DURATION_MS) // EVENTS_PER_HALF
            clock = (half - 1) * HALF_DURATION_MS + offset
            team = teams[(position // 8 + half - 1) % 2]
            opponent = teams[1] if team == teams[0] else teams[0]
            phase = position % 8
            kind = (
                EventType.TURNOVER if phase == 0 else
                EventType.CARRY if phase in (1, 4) else
                EventType.SHOT if phase == 7 else EventType.PASS
            )
            if kind == EventType.TURNOVER:
                outcome = Outcome.SUCCESS
            elif kind == EventType.SHOT:
                outcome = Outcome.SUCCESS if (index + seed) % 41 == 0 else Outcome.FAILURE
                if outcome == Outcome.SUCCESS:
                    kind = EventType.GOAL
            else:
                outcome = Outcome.SUCCESS
            x = rng.randrange(18, 92) if kind not in (EventType.SHOT, EventType.GOAL) else rng.randrange(81, 103)
            y = rng.randrange(8, 61)
            destination = (
                Point(x=105, y=34)
                if kind in (EventType.SHOT, EventType.GOAL) else
                Point(x=min(104, x + rng.randrange(1, 12)), y=min(67, y + rng.randrange(-5, 6)))
                if kind in (EventType.PASS, EventType.CARRY) else None
            )
            evidence: dict[str, str | int | float | bool] = {
                "fixture": "seeded_uncalibrated",
                "phase": phase,
            }
            if kind == EventType.TURNOVER:
                evidence["possession_change"] = True
            events.append(MatchEvent(
                match_id=match.match_id,
                event_id=f"{match.match_id}-e{index:04d}",
                sequence=index,
                period=half,
                clock_ms=clock,
                observed_at=start + timedelta(milliseconds=clock),
                team_id=team,
                player_id=f"{'harbor' if team == teams[0] else 'ridge'}-{1 + position % 11}",
                event_type=kind,
                outcome=outcome,
                location=Point(x=x, y=y),
                destination=destination,
                possession_team_id=team if kind != EventType.TURNOVER else team,
                evidence=evidence,
                provenance=provenance,
            ))
    validate_stream(events, match)
    return match, events
