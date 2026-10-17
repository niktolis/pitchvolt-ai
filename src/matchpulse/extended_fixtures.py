"""Repeatable two-half football-like replay fixtures for navigation testing.

These sequences are original fictional test data, not historical observations.
Only broad action frequencies are calibrated to one pinned StatsBomb match.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
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
from matchpulse.simulation import MATCH
from matchpulse.statsbomb_reference import calibrated_action_quotas

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
    action_quotas = calibrated_action_quotas(EVENTS_PER_HALF * 2 - 4)
    # Script one eight-event press-to-goal burst. Subtract every scripted
    # action from reference quotas to preserve overall action counts.
    scripted = {
        71: EventType.CARRY,
        72: EventType.PASS,
        73: EventType.PRESSURE,
        74: EventType.PASS,
        75: EventType.TURNOVER,
        76: EventType.CARRY,
        77: EventType.PASS,
        78: EventType.SHOT,
    }
    for kind in scripted.values():
        if kind != EventType.TURNOVER:
            action_quotas[kind] -= 1
    slots: list[EventType | None] = [None] * (EVENTS_PER_HALF * 2)
    for index, kind in scripted.items():
        slots[index - 1] = kind
    for index in (20, 145, 200):
        slots[index - 1] = EventType.TURNOVER
    remaining = [kind for kind, count in action_quotas.items() for _ in range(count)]
    rng.shuffle(remaining)
    pending = iter(remaining)
    planned = [kind if kind is not None else next(pending) for kind in slots]
    assert len(planned) == EVENTS_PER_HALF * 2
    possession = teams[0]
    for half in (1, 2):
        for position in range(EVENTS_PER_HALF):
            index = len(events) + 1
            # Include sparse time windows and two stable halves. Every event is
            # grounded in the synthetic generation seed and absolute match clock.
            offset = (position * HALF_DURATION_MS) // EVENTS_PER_HALF
            clock = (half - 1) * HALF_DURATION_MS + offset
            if 71 <= index <= 78:
                # All eight causal events fit the detector's 45-second window.
                clock = (69 * HALF_DURATION_MS) // EVENTS_PER_HALF + (index - 70) * 2_500
            phase = position % 8
            kind = planned[index - 1]
            if kind == EventType.TURNOVER:
                possession = teams[1] if possession == teams[0] else teams[0]
            team = (
                teams[1] if possession == teams[0] else teams[0]
            ) if kind == EventType.PRESSURE else possession
            outcome = Outcome.SUCCESS
            if kind == EventType.SHOT:
                if index == 78:
                    kind = EventType.GOAL
                else:
                    outcome = Outcome.FAILURE
            x = rng.randrange(18, 92) if kind not in (EventType.SHOT, EventType.GOAL) else rng.randrange(81, 103)
            y = rng.randrange(8, 61)
            destination = (
                Point(x=105, y=34)
                if kind in (EventType.SHOT, EventType.GOAL) else
                Point(x=min(104, x + rng.randrange(1, 12)), y=min(67, y + rng.randrange(-5, 6)))
                if kind in (EventType.PASS, EventType.CARRY) else None
            )
            evidence: dict[str, str | int | float | bool] = {
                "fixture": "statsbomb_reference_weighted_actions",
                "phase": phase,
            }
            if kind == EventType.TURNOVER:
                evidence["possession_change"] = True
            if index == 74:
                outcome = Outcome.FAILURE
                evidence["under_pressure"] = True
            if 71 <= index <= 78:
                evidence["scripted_tactical_window"] = True
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
                possession_team_id=possession,
                evidence=evidence,
                provenance=provenance,
            ))
    validate_stream(events, match)
    return match, events
