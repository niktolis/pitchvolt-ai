"""Pinned, event-linked StatsBomb 360 observations, never synthetic tracking.

360 freezes only capture players *visible* at a source event. Except for the
event actor, observations contain no player IDs and cannot be associated with
persistent roster entries or interpolated across events.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from matchpulse.events import Point
from matchpulse.fixture_manifest import FixtureOrigin
from matchpulse.providers.statsbomb import (
    STATSBOMB_LENGTH,
    STATSBOMB_WIDTH,
    statsbomb_to_point,
)
from matchpulse.providers.statsbomb_historical import HistoricalFixture
from matchpulse.providers.statsbomb_projection import historical_clock_ms


@dataclass(frozen=True)
class Observed360Player:
    """Anonymous per-frame detection; player_id known only for the source actor."""

    observation_index: int
    position: Point | None
    source_location: tuple[float, float]
    teammate: bool
    actor: bool
    keeper: bool
    player_id: int | None


@dataclass(frozen=True)
class Historical360Frame:
    event_id: str
    period: int
    clock_ms: int
    event_team_id: int
    visible_area: tuple[float, ...]
    observations: tuple[Observed360Player, ...]

    @property
    def has_observed_full_xi(self) -> bool:
        """Exact 11/11 snapshot, not continuous or identified tracking."""
        return (
            len(self.observations) == 22
            and sum(p.teammate for p in self.observations) == 11
            and sum(not p.teammate for p in self.observations) == 11
        )


@dataclass(frozen=True)
class Historical360Bundle:
    match_id: str
    event_sha256: str
    frame_sha256: str
    frames: tuple[Historical360Frame, ...]

    def at_event(self, event_id: str) -> Historical360Frame | None:
        """Exact-event selection only. Never reuse future or previous observations."""
        return next((frame for frame in self.frames if frame.event_id == event_id), None)


def _number(value: Any, field: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"Invalid StatsBomb 360 {field}")
    return float(value)


def _frame(record: dict[str, Any], event: dict[str, Any]) -> Historical360Frame:
    raw_area = record.get("visible_area")
    if not isinstance(raw_area, list) or len(raw_area) < 6 or len(raw_area) % 2:
        raise ValueError("Invalid StatsBomb 360 visible_area polygon")
    area = tuple(_number(v, "visible_area") for v in raw_area)
    raw_players = record.get("freeze_frame")
    if not isinstance(raw_players, list) or len(raw_players) > 22:
        raise ValueError("Invalid StatsBomb 360 freeze_frame count")

    team = event.get("team")
    if not isinstance(team, dict) or type(team.get("id")) is not int:
        raise ValueError("StatsBomb 360 event missing source team ID")
    source_actor = event.get("player")
    actor_id = source_actor.get("id") if isinstance(source_actor, dict) else None
    if actor_id is not None and (type(actor_id) is not int or actor_id <= 0):
        raise ValueError("Invalid source actor identity")

    observations: list[Observed360Player] = []
    for index, item in enumerate(raw_players):
        if not isinstance(item, dict):
            raise TypeError("Invalid StatsBomb 360 player observation")
        if any(type(item.get(flag)) is not bool for flag in ("teammate", "actor", "keeper")):
            raise ValueError("StatsBomb 360 observation requires exact boolean flags")
        if item["actor"] and not item["teammate"]:
            raise ValueError("StatsBomb 360 actor must belong to event team")
        location = item.get("location")
        if not isinstance(location, list) or len(location) != 2:
            raise ValueError("Invalid StatsBomb 360 player location")
        # Reuse the canonical 120x80 -> 105x68 normalization contract.
        x = _number(location[0], "x")
        y = _number(location[1], "y")
        # Some genuine camera observations are marginally off the pitch.
        # Preserve the original measurement. Do NOT clamp to a fake on-field point.
        on_pitch = 0 <= x <= STATSBOMB_LENGTH and 0 <= y <= STATSBOMB_WIDTH
        point = statsbomb_to_point([x, y]) if on_pitch else None
        observations.append(Observed360Player(
            observation_index=index,
            position=point,
            source_location=(x, y),
            teammate=item["teammate"],
            actor=item["actor"],
            keeper=item["keeper"],
            player_id=actor_id if item["actor"] else None,
        ))

    if sum(p.actor for p in observations) > 1:
        raise ValueError("Multiple StatsBomb 360 actors for one event")
    if any(
        sum(p.keeper and p.teammate == side for p in observations) > 1
        for side in (True, False)
    ):
        raise ValueError("Multiple keepers for same StatsBomb 360 side")
    if any(
        sum(p.teammate == side for p in observations) > 11
        for side in (True, False)
    ):
        raise ValueError("StatsBomb 360 side exceeds eleven observed players")

    return Historical360Frame(
        event_id=event["id"],
        period=event["period"],
        clock_ms=historical_clock_ms(event),
        event_team_id=team["id"],
        visible_area=area,
        observations=tuple(observations),
    )


def load_historical_360(
    path: Path,
    fixture: HistoricalFixture,
    *,
    expected_sha256: str,
) -> Historical360Bundle:
    """Validate exact original 360 bytes, event membership and source origin.

    Uses no network or ambient configuration, and is not a hosted synthetic API.
    Caller must independently verify that the event and 360 files are from the
    same upstream revision and match. No match-9880 360 file is assumed.
    """
    if fixture.manifest.origin != FixtureOrigin.STATSBOMB_OPEN_DATA:
        raise ValueError("StatsBomb 360 requires verified historical origin")
    if path.name != f"{fixture.manifest.match_id}.360.json":
        raise ValueError("StatsBomb 360 filename/match ID mismatch")
    if len(expected_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in expected_sha256):
        raise ValueError("Invalid pinned StatsBomb 360 SHA-256")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError("StatsBomb 360 SHA-256 mismatch")
    decoded = json.loads(raw)
    if not isinstance(decoded, list) or not decoded:
        raise ValueError("StatsBomb 360 source must contain event frames")

    by_id = {event["id"]: event for event in fixture.records}
    seen: set[str] = set()
    frames: list[Historical360Frame] = []
    for item in decoded:
        if not isinstance(item, dict) or not isinstance(item.get("event_uuid"), str):
            raise TypeError("Invalid StatsBomb 360 event_uuid")
        event_id = item["event_uuid"]
        if event_id in seen:
            raise ValueError("Duplicate StatsBomb 360 event frame")
        if event_id not in by_id:
            raise ValueError("StatsBomb 360 event UUID absent from source events")
        seen.add(event_id)
        frames.append(_frame(item, by_id[event_id]))
    return Historical360Bundle(
        match_id=fixture.manifest.match_id,
        event_sha256=fixture.manifest.event_sha256,
        frame_sha256=digest,
        frames=tuple(frames),
    )
