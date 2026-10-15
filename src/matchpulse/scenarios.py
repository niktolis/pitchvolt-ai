"""Original synthetic football scenarios, using the shared canonical event model."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from random import Random

from matchpulse.events import (
    EventType, MatchEvent, MatchMetadata, Outcome, Point, Provenance, validate_stream,
)
from matchpulse.simulation import MATCH, high_press_replay


def _scenario(
    name: str,
    seed: int,
    steps: list[tuple[EventType, str, str, Outcome, tuple[int, int], tuple[int, int] | None, str, dict[str, str | int | float | bool]]],
) -> tuple[MatchMetadata, list[MatchEvent]]:
    """One canonical constructor for synthetic fixture events; no copied schemas."""
    rng = Random(seed)
    match = MatchMetadata(
        match_id=f"synthetic-{name}-{seed}",
        home_team_id=MATCH.home_team_id,
        away_team_id=MATCH.away_team_id,
    )
    start = datetime(2026, 1, 1, tzinfo=UTC)
    provenance = Provenance(
        generator="matchpulse-scenarios", generator_version="0.1.0", seed=seed, scenario=name
    )
    events = [
        MatchEvent(
            match_id=match.match_id,
            event_id=f"{match.match_id}-e{i:03d}",
            sequence=i,
            period=2,
            clock_ms=4_200_000 + i * 3_000 + rng.randint(0, 500),
            observed_at=start + timedelta(milliseconds=4_200_000 + i * 3_000),
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
        for i, (kind, team, player, outcome, pos, dest, possession, evidence)
        in enumerate(steps, start=1)
    ]
    validate_stream(events, match)
    return match, events


def scenario(name: str, seed: int = 42) -> tuple[MatchMetadata, list[MatchEvent]]:
    """Fixtures model causal transitions; not a physics-driven full match simulation."""
    home, away = MATCH.home_team_id, MATCH.away_team_id
    if name == "high_press":
        base = high_press_replay(seed)
        metadata = MATCH.model_copy(update={"match_id": f"synthetic-high-press-{seed}"})
        events = [
            event.model_copy(update={
                "match_id": metadata.match_id,
                "event_id": f"{metadata.match_id}-e{i:03d}",
            })
            for i, event in enumerate(base, 1)
        ]
        validate_stream(events, metadata)
        return metadata, events
    if name == "counterattack":
        return _scenario(name, seed, [
            (EventType.CARRY, away, "ridge-6", Outcome.SUCCESS, (24, 25), (35, 30), away, {}),
            (EventType.TURNOVER, home, "harbor-5", Outcome.SUCCESS, (35, 30), None, home, {}),
            (EventType.CARRY, home, "harbor-7", Outcome.SUCCESS, (35, 30), (72, 32), home, {}),
            (EventType.PASS, home, "harbor-7", Outcome.SUCCESS, (72, 32), (96, 36), home, {}),
            (EventType.SHOT, home, "harbor-9", Outcome.FAILURE, (96, 36), (105, 34), home, {}),
        ])
    if name == "sustained_possession":
        return _scenario(name, seed, [
            (EventType.PASS, home, "harbor-4", Outcome.SUCCESS, (25, 24), (38, 31), home, {}),
            (EventType.PASS, home, "harbor-6", Outcome.SUCCESS, (38, 31), (52, 24), home, {}),
            (EventType.CARRY, home, "harbor-8", Outcome.SUCCESS, (52, 24), (63, 25), home, {}),
            (EventType.PASS, home, "harbor-8", Outcome.SUCCESS, (63, 25), (79, 32), home, {}),
            (EventType.PASS, home, "harbor-10", Outcome.SUCCESS, (79, 32), (91, 35), home, {}),
            (EventType.SHOT, home, "harbor-9", Outcome.FAILURE, (91, 35), (105, 34), home, {}),
        ])
    raise ValueError(f"Unknown synthetic scenario: {name}")
