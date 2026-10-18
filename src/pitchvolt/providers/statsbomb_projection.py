"""Conservative presentation projection for historical StatsBomb Open Data.

This deliberately does NOT call MatchProcessor or claim complete canonical
MatchEvent compatibility: real-match provenance, missing locations, and
possession semantics need separate source-aware contracts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pitchvolt.providers.statsbomb import statsbomb_to_point
from pitchvolt.providers.statsbomb_historical import HistoricalFixture

_PROJECTIONS = frozenset({"Pass", "Pressure", "Carry", "Shot"})
_DESTINATIONS = {"Pass": "pass", "Carry": "carry", "Shot": "shot"}


@dataclass(frozen=True)
class HistoricalAction:
    event_id: str
    index: int
    period: int
    clock_ms: int
    team: str
    player: str
    kind: str
    location_x: float
    location_y: float
    destination_x: float | None = None
    destination_y: float | None = None
    source_outcome: str | None = None
    is_goal: bool = False


@dataclass(frozen=True)
class HistoricalProjection:
    actions: tuple[HistoricalAction, ...]
    omitted_by_type: dict[str, int]
    source_event_count: int
    complete: bool


def _name(value: Any) -> str | None:
    if isinstance(value, dict) and isinstance(value.get("name"), str):
        return value["name"]
    return None


def historical_clock_ms(event: dict[str, Any]) -> int:
    minute, second = event.get("minute"), event.get("second")
    timestamp = event.get("timestamp")
    if (type(minute) is not int or minute < 0 or type(second) is not int
            or not 0 <= second < 60 or not isinstance(timestamp, str)):
        raise ValueError("Historical clock missing or invalid")
    # The period-relative source timestamp supplies fractions; StatsBomb's
    # minute/second fields are the match-relative display clock.
    pieces = timestamp.split(":")
    if len(pieces) != 3 or "." not in pieces[2]:
        raise ValueError("Historical timestamp lacks millisecond precision")
    fractional = pieces[2].split(".", 1)[1]
    if not fractional.isdigit() or len(fractional) > 6 or not fractional:
        raise ValueError("Invalid historical fractional timestamp")
    return (minute * 60 + second) * 1000 + int((fractional + "000")[:3])


def project_historical_actions(fixture: HistoricalFixture) -> HistoricalProjection:
    """Map only source-backed pitch actions; disclose every omission explicitly.

    Never infer a turnover, goal or score from a ball recovery or other sparse
    event. Missing player/location is an omission, not a fabricated placeholder.
    """
    actions: list[HistoricalAction] = []
    omitted: dict[str, int] = {}
    previous_clock = -1
    previous_period = 0
    for event in fixture.records:
        kind = _name(event["type"])
        assert kind is not None  # validated by historical fixture loader
        clock = historical_clock_ms(event)
        period = event["period"]
        if period < previous_period or (period == previous_period and clock < previous_clock):
            raise ValueError("Historical projected events out of match clock order")
        previous_period, previous_clock = period, clock
        if kind not in _PROJECTIONS:
            omitted[kind] = omitted.get(kind, 0) + 1
            continue
        team, player = _name(event.get("team")), _name(event.get("player"))
        location = event.get("location")
        if not team or not player or not isinstance(location, list):
            omitted[kind] = omitted.get(kind, 0) + 1
            continue
        origin = statsbomb_to_point(location)
        destination = None
        field = _DESTINATIONS.get(kind)
        detail = event.get(field) if field else None
        if field and isinstance(detail, dict) and isinstance(detail.get("end_location"), list):
            destination = statsbomb_to_point(detail["end_location"])
        elif field and kind != "Shot":
            omitted[kind] = omitted.get(kind, 0) + 1
            continue
        # StatsBomb shots can lack end_location. The source shot still occurred;
        # omitting it would hide match action. Do not fabricate a target point.
        source_outcome = _name(detail.get("outcome")) if isinstance(detail, dict) else None
        actions.append(HistoricalAction(
            event_id=event["id"], index=event["index"], period=period,
            clock_ms=clock, team=team, player=player, kind=kind.lower(),
            location_x=origin.x, location_y=origin.y,
            destination_x=destination.x if destination else None,
            destination_y=destination.y if destination else None,
            source_outcome=source_outcome,
            is_goal=kind == "Shot" and source_outcome == "Goal",
        ))
    return HistoricalProjection(
        actions=tuple(actions), omitted_by_type=dict(sorted(omitted.items())),
        source_event_count=len(fixture.records), complete=not omitted,
    )
