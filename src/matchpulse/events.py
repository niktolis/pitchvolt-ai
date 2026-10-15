"""Provider-neutral, versioned canonical football event contract."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EventType(StrEnum):
    PASS = "pass"
    PRESSURE = "pressure"
    TURNOVER = "turnover"
    CARRY = "carry"
    SHOT = "shot"
    GOAL = "goal"


class Outcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"


class Point(BaseModel):
    model_config = ConfigDict(frozen=True)

    x: Annotated[float, Field(ge=0, le=105)]
    y: Annotated[float, Field(ge=0, le=68)]


class Provenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str = "synthetic"
    generator: str
    generator_version: str
    seed: int
    scenario: str

    @model_validator(mode="after")
    def synthetic_only(self) -> "Provenance":
        if self.source != "synthetic":
            raise ValueError("MVP events must originate from synthetic data")
        return self


class MatchEvent(BaseModel):
    """Pitch coordinates follow a provider-neutral 105m x 68m convention."""

    model_config = ConfigDict(frozen=True)

    schema_version: Annotated[int, Field(ge=1)] = 1
    match_id: str
    event_id: str
    sequence: Annotated[int, Field(ge=1)]
    period: Annotated[int, Field(ge=1, le=2)]
    clock_ms: Annotated[int, Field(ge=0)]
    observed_at: datetime
    team_id: str
    player_id: str
    event_type: EventType
    outcome: Outcome
    location: Point
    destination: Point | None = None
    possession_team_id: str
    evidence: dict[str, str | int | float | bool] = Field(default_factory=dict)
    provenance: Provenance

    @model_validator(mode="after")
    def validate_semantics(self) -> "MatchEvent":
        if not self.match_id or not self.event_id or not self.team_id or not self.player_id:
            raise ValueError("Identity fields must not be empty")
        if self.event_type == EventType.PASS and self.destination is None:
            raise ValueError("Pass requires a destination")
        if self.event_type in (EventType.SHOT, EventType.GOAL) and self.destination is None:
            raise ValueError("Shot/goal requires a destination")
        if self.event_type == EventType.GOAL and self.outcome != Outcome.SUCCESS:
            raise ValueError("Goal event must succeed")
        return self


class MatchMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    match_id: str
    home_team_id: str
    away_team_id: str
    pitch_length_m: float = 105
    pitch_width_m: float = 68

    @model_validator(mode="after")
    def different_teams(self) -> "MatchMetadata":
        if self.home_team_id == self.away_team_id:
            raise ValueError("Match requires two distinct teams")
        return self


class EventSource(Protocol):
    """Adapters emit canonical events; the domain never sees provider schemas."""

    def events(self) -> list[MatchEvent]: ...


def validate_stream(events: list[MatchEvent], match: MatchMetadata) -> None:
    """Enforce stream-level invariants independent of provider or simulator."""
    seen: set[str] = set()
    previous_key: tuple[int, int] | None = None
    teams = {match.home_team_id, match.away_team_id}
    for expected_sequence, event in enumerate(events, start=1):
        if event.match_id != match.match_id:
            raise ValueError("Event belongs to another match")
        if event.sequence != expected_sequence:
            raise ValueError("Non-contiguous event sequence")
        if event.event_id in seen:
            raise ValueError("Duplicate event ID")
        if event.team_id not in teams or event.possession_team_id not in teams:
            raise ValueError("Unknown team ID")
        key = (event.period, event.clock_ms)
        if previous_key is not None and key < previous_key:
            raise ValueError("Events out of match-clock order")
        previous_key = key
        seen.add(event.event_id)
