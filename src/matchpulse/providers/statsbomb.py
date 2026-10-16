"""StatsBomb-shaped *fictional* event boundary.

This is a deliberately strict synthetic subset of Hudl/StatsBomb Open Data's
event JSON format, not a general-purpose historical-data importer. Never
relabel downloaded Open Data as synthetic.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from math import isfinite
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field

from matchpulse.events import (
    PITCH_LENGTH_M,
    PITCH_WIDTH_M,
    EventType,
    MatchEvent,
    MatchMetadata,
    Outcome,
    Point,
    Provenance,
    validate_stream,
)

STATSBOMB_LENGTH = 120.0
STATSBOMB_WIDTH = 80.0
CANONICAL_LENGTH_M = PITCH_LENGTH_M
CANONICAL_WIDTH_M = PITCH_WIDTH_M

# Only these *synthetic* event families have reviewed semantics.
_TYPE_TO_KIND = {
    "Pressure": EventType.PRESSURE,
    "Pass": EventType.PASS,
    "Ball Recovery": EventType.TURNOVER,
    "Carry": EventType.CARRY,
    "Shot": EventType.SHOT,
}
_TYPE_IDS = {"Pressure": 17, "Pass": 30, "Ball Recovery": 2, "Carry": 43, "Shot": 16}
_TYPE_BY_KIND = {
    EventType.PRESSURE: "Pressure",
    EventType.PASS: "Pass",
    EventType.TURNOVER: "Ball Recovery",
    EventType.CARRY: "Carry",
    EventType.SHOT: "Shot",
    EventType.GOAL: "Shot",
}
_PASS_OUTCOMES = {
    "Incomplete": 9, "Out": 75, "Pass Offside": 76,
}
_SHOT_OUTCOMES = {
    "Blocked": 96, "Goal": 97, "Off T": 98, "Post": 99,
    "Saved": 100, "Wayward": 101, "Saved Off Target": 115,
    "Saved to Post": 116,
}


class SBRef(BaseModel):
    id: int
    name: str = Field(min_length=1)


class SBPass(BaseModel):
    end_location: list[float] = Field(min_length=2, max_length=2)
    outcome: SBRef | None = None


class SBCarry(BaseModel):
    end_location: list[float] = Field(min_length=2, max_length=2)


class SBShot(BaseModel):
    end_location: list[float] = Field(min_length=2, max_length=3)
    outcome: SBRef


class SBBallRecovery(BaseModel):
    recovery_failure: bool = False


class SBEvent(BaseModel):
    """Reviewed projection of raw StatsBomb JSON; unrelated fields are permitted."""

    model_config = ConfigDict(extra="allow")

    id: UUID
    index: int = Field(ge=1)
    period: int = Field(ge=1, le=2)
    timestamp: str
    minute: int = Field(ge=0)
    second: int = Field(ge=0, le=59)
    type: SBRef
    team: SBRef
    player: SBRef
    possession: int = Field(ge=1)
    possession_team: SBRef
    location: list[float] = Field(min_length=2, max_length=2)
    under_pressure: bool = False
    pass_: SBPass | None = Field(default=None, alias="pass")
    carry: SBCarry | None = None
    shot: SBShot | None = None
    ball_recovery: SBBallRecovery | None = None


def statsbomb_to_point(coordinates: list[float] | tuple[float, ...]) -> Point:
    """Provider pitch coordinates (120 × 80) -> canonical physical metres."""
    if len(coordinates) < 2 or len(coordinates) > 3:
        raise ValueError("Expected two StatsBomb coordinates (or shot x/y/z)")
    x, y = coordinates[:2]
    if (
        isinstance(x, bool) or isinstance(y, bool)
        or not isfinite(x) or not isfinite(y)
        or not (0 <= x <= STATSBOMB_LENGTH and 0 <= y <= STATSBOMB_WIDTH)
    ):
        raise ValueError("StatsBomb pitch coordinates outside 120 × 80")
    return Point(
        x=round(x * CANONICAL_LENGTH_M / STATSBOMB_LENGTH, 6),
        y=round(y * CANONICAL_WIDTH_M / STATSBOMB_WIDTH, 6),
    )


def point_to_statsbomb(point: Point) -> list[float]:
    """Convert physical pitch metres to StatsBomb's provider grid."""
    return [
        round(point.x * STATSBOMB_LENGTH / CANONICAL_LENGTH_M, 6),
        round(point.y * STATSBOMB_WIDTH / CANONICAL_WIDTH_M, 6),
    ]


def _clock_ms(event: SBEvent) -> int:
    # StatsBomb 'timestamp' is period-relative, while 'minute' is the
    # absolute match minute. The timestamp supplies millisecond precision.
    try:
        parts = event.timestamp.split(":")
        if len(parts) != 3 or "." not in parts[2]:
            raise ValueError("Missing timestamp milliseconds")
        hours, minutes = int(parts[0]), int(parts[1])
        seconds, fraction = parts[2].split(".", 1)
        if (len(fraction) != 3 or not fraction.isdigit() or
            hours < 0 or not 0 <= minutes < 60 or not 0 <= int(seconds) < 60):
            raise ValueError("Invalid period timestamp")
        if int(seconds) != event.second:
            raise ValueError("Second does not match period timestamp")
        # A source timestamp is local to its period (0 or 45 minutes offset).
        period_start_minute = 45 if event.period == 2 else 0
        if hours * 60 + minutes != event.minute - period_start_minute:
            raise ValueError("StatsBomb timestamp disagrees with match minute")
        return (event.minute * 60 + event.second) * 1000 + int(fraction)
    except (ValueError, IndexError) as exc:
        raise ValueError(f"Invalid StatsBomb timestamp: {event.timestamp}: {exc}") from exc


def _outcome(event: SBEvent, kind: EventType) -> Outcome:
    if kind == EventType.PASS:
        if event.pass_ is None:
            raise ValueError("StatsBomb Pass requires pass.end_location")
        outcome = event.pass_.outcome
        if outcome is None:
            return Outcome.SUCCESS
        if outcome.name not in _PASS_OUTCOMES:
            raise ValueError(f"Unsupported StatsBomb pass outcome: {outcome.name}")
        if outcome.id != _PASS_OUTCOMES[outcome.name]:
            raise ValueError("StatsBomb pass outcome ID/name mismatch")
        return Outcome.FAILURE
    if kind == EventType.SHOT:
        if event.shot is None:
            raise ValueError("StatsBomb Shot requires shot.outcome and end_location")
        if event.shot.outcome.name not in _SHOT_OUTCOMES:
            raise ValueError(f"Unsupported StatsBomb shot outcome: {event.shot.outcome.name}")
        if event.shot.outcome.id != _SHOT_OUTCOMES[event.shot.outcome.name]:
            raise ValueError("StatsBomb shot outcome ID/name mismatch")
        return Outcome.SUCCESS if event.shot.outcome.name == "Goal" else Outcome.FAILURE
    if kind == EventType.PRESSURE:
        return Outcome.NEUTRAL
    return Outcome.SUCCESS


class StatsBombSyntheticSource:
    """A strict EventSource adapter for original, fictional StatsBomb-style JSON."""

    def __init__(
        self,
        match: MatchMetadata,
        records: list[dict[str, object]],
        provenance: Provenance,
        observed_at_base: datetime = datetime(2026, 1, 1, tzinfo=UTC),
    ) -> None:
        if provenance.source != "synthetic":
            raise ValueError("Only originally synthetic StatsBomb-shaped input is permitted")
        if observed_at_base.tzinfo is None:
            raise ValueError("observed_at_base must be timezone-aware")
        self.match = match
        self.records = records
        self.provenance = provenance
        self.observed_at_base = observed_at_base

    def events(self) -> list[MatchEvent]:
        converted: list[MatchEvent] = []
        previous_possession: int | None = None
        names_by_id: dict[int, str] = {}
        ids_by_name: dict[str, int] = {}
        for sequence, raw in enumerate(self.records, 1):
            event = SBEvent.model_validate(raw)
            if event.index != sequence:
                raise ValueError("StatsBomb indices must be contiguous starting at 1")
            if event.type.name not in _TYPE_TO_KIND:
                raise ValueError(f"Unsupported StatsBomb event: {event.type.name}")
            if event.type.id != _TYPE_IDS[event.type.name]:
                raise ValueError("StatsBomb event type ID/name mismatch")
            if previous_possession is not None and event.possession < previous_possession:
                raise ValueError("StatsBomb possession counter moved backward")
            prior_possession = previous_possession
            previous_possession = event.possession

            for reference in (event.team, event.possession_team, event.player):
                old_name = names_by_id.setdefault(reference.id, reference.name)
                old_id = ids_by_name.setdefault(reference.name, reference.id)
                if old_name != reference.name or old_id != reference.id:
                    raise ValueError("Inconsistent StatsBomb reference ID/name mapping")
            kind = _TYPE_TO_KIND[event.type.name]
            outcome = _outcome(event, kind)
            if kind == EventType.SHOT and outcome == Outcome.SUCCESS:
                kind = EventType.GOAL
            if kind == EventType.TURNOVER and (
                event.ball_recovery is not None and event.ball_recovery.recovery_failure
            ):
                raise ValueError("Failed Ball Recovery cannot become a turnover")
            if kind == EventType.TURNOVER:
                if event.team.name != event.possession_team.name:
                    raise ValueError("Ball Recovery must award possession to recovering team")
                if converted and (
                    event.possession_team.name == converted[-1].possession_team_id
                    or (prior_possession is not None and event.possession <= prior_possession)
                ):
                    raise ValueError("Turnover requires new team and new possession ID")

            destination_raw: list[float] | None = None
            if kind == EventType.PASS:
                assert event.pass_ is not None
                destination_raw = event.pass_.end_location
            elif kind == EventType.CARRY:
                if event.carry is None:
                    raise ValueError("StatsBomb Carry requires carry.end_location")
                destination_raw = event.carry.end_location
            elif kind in (EventType.SHOT, EventType.GOAL):
                assert event.shot is not None
                destination_raw = event.shot.end_location

            clock = _clock_ms(event)
            evidence: dict[str, str | int | float | bool] = {}
            if event.under_pressure:
                evidence["under_pressure"] = True
            if event.shot is not None:
                evidence["on_target"] = event.shot.outcome.name in {"Saved", "Saved to Post", "Goal"}
            converted.append(MatchEvent(
                match_id=self.match.match_id,
                event_id=str(event.id),
                sequence=sequence,
                period=event.period,
                clock_ms=clock,
                observed_at=self.observed_at_base + timedelta(milliseconds=clock),
                team_id=event.team.name,
                player_id=event.player.name,
                event_type=kind,
                outcome=outcome,
                location=statsbomb_to_point(event.location),
                destination=statsbomb_to_point(destination_raw) if destination_raw else None,
                possession_team_id=event.possession_team.name,
                evidence=evidence,
                provenance=self.provenance,
            ))
        validate_stream(converted, self.match)
        # Enforce stateful possession rules, not merely schema validity. No implicit
        # turnover is inferred from StatsBomb possession sequence increments.
        from matchpulse.intelligence import MatchProcessor

        processor = MatchProcessor(self.match)
        for converted_event in converted:
            processor.ingest(converted_event)
        return converted


def synthetic_to_statsbomb(match: MatchMetadata, events: list[MatchEvent]) -> list[dict[str, object]]:
    """Export original MatchPulse fiction in a StatsBomb-shaped event JSON subset.

    These records are NOT data downloaded from Hudl/StatsBomb.
    """
    validate_stream(events, match)
    teams = {match.home_team_id: 1, match.away_team_id: 2}
    players = {player: i for i, player in enumerate(sorted({e.player_id for e in events}), 1001)}
    possession = 1
    output: list[dict[str, object]] = []
    for e in events:
        if e.event_type == EventType.TURNOVER:
            possession += 1
        kind = _TYPE_BY_KIND[e.event_type]
        local_ms = e.clock_ms - (45 * 60_000 if e.period == 2 else 0)
        if local_ms < 0:
            raise ValueError("Second-half clock precedes minute 45")
        hours, rest = divmod(local_ms, 3_600_000)
        minutes, rest = divmod(rest, 60_000)
        seconds, milliseconds = divmod(rest, 1000)
        raw: dict[str, object] = {
            "id": str(uuid5(NAMESPACE_URL, f"matchpulse-synthetic:{e.event_id}")),
            "index": e.sequence,
            "period": e.period,
            "timestamp": f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}",
            "minute": e.clock_ms // 60_000,
            "second": (e.clock_ms // 1000) % 60,
            "type": {"id": _TYPE_IDS[kind], "name": kind},
            "team": {"id": teams[e.team_id], "name": e.team_id},
            "player": {"id": players[e.player_id], "name": e.player_id},
            "possession": possession,
            "possession_team": {
                "id": teams[e.possession_team_id], "name": e.possession_team_id,
            },
            "location": point_to_statsbomb(e.location),
        }
        if e.evidence.get("under_pressure") is True:
            raw["under_pressure"] = True
        if e.event_type == EventType.PASS:
            if e.destination is None:
                raise ValueError("Pass destination required")
            p: dict[str, object] = {"end_location": point_to_statsbomb(e.destination)}
            if e.outcome == Outcome.FAILURE:
                p["outcome"] = {"id": 9, "name": "Incomplete"}
            elif e.outcome != Outcome.SUCCESS:
                raise ValueError("Neutral pass has no lossless StatsBomb mapping")
            raw["pass"] = p
        elif e.event_type == EventType.CARRY:
            if e.destination is None:
                raise ValueError("Carry destination required for StatsBomb export")
            raw["carry"] = {"end_location": point_to_statsbomb(e.destination)}
        elif e.event_type in (EventType.SHOT, EventType.GOAL):
            if e.destination is None:
                raise ValueError("Shot destination required")
            shot_outcome = (
                {"id": 97, "name": "Goal"} if e.event_type == EventType.GOAL
                else {"id": 100, "name": "Saved"} if e.evidence.get("on_target")
                else {"id": 98, "name": "Off T"}
            )
            raw["shot"] = {
                "end_location": point_to_statsbomb(e.destination),
                "outcome": shot_outcome,
            }
        elif e.event_type == EventType.TURNOVER:
            raw["ball_recovery"] = {}
        output.append(raw)
    return output
