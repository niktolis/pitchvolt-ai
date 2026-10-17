"""Event-exact, independently verified StatsBomb 360 replay observations.

Historical source observations are never relabelled as fictional MatchEvents,
interpolated in time, or reused at a different replay cursor.
"""
from __future__ import annotations

from dataclasses import dataclass

from matchpulse.fixture_manifest import FixtureOrigin
from matchpulse.providers.statsbomb_360 import (
    Historical360Bundle,
    Historical360Frame,
    Observed360Player,
)
from matchpulse.providers.statsbomb_historical import HistoricalFixture
from matchpulse.providers.statsbomb_projection import historical_clock_ms


@dataclass(frozen=True)
class HistoricalReplayMoment:
    match_id: str
    event_id: str
    clock_ms: int
    period: int
    event_sha256: str
    frame_sha256: str
    frame: Historical360Frame | None

    @property
    def observed(self) -> tuple[Observed360Player, ...]:
        """No frame means no observations: never carry actors or players forward."""
        return self.frame.observations if self.frame else ()

    @property
    def renderable(self) -> tuple[Observed360Player, ...]:
        """Preserve off-pitch observations without drawing fake edge positions."""
        return tuple(p for p in self.observed if p.position is not None)

    @property
    def full_xi(self) -> bool:
        return self.frame is not None and self.frame.has_observed_full_xi


def historical_moment_at_event(
    fixture: HistoricalFixture,
    frames: Historical360Bundle,
    event_id: str,
) -> HistoricalReplayMoment:
    """Join by source UUID with strict match/hash and clock/period validation."""
    if fixture.manifest.origin != FixtureOrigin.STATSBOMB_OPEN_DATA:
        raise ValueError("Historical replay requires verified source origin")
    if frames.match_id != fixture.manifest.match_id:
        raise ValueError("Historical replay match identity mismatch")
    if frames.event_sha256 != fixture.manifest.event_sha256:
        raise ValueError("Historical replay source event fingerprint mismatch")
    event = next((record for record in fixture.records if record["id"] == event_id), None)
    if event is None:
        raise ValueError("Historical replay event UUID absent from verified fixture")
    frame = frames.at_event(event_id)
    clock_ms = historical_clock_ms(event)
    if frame is not None and (
        frame.event_id != event_id or frame.clock_ms != clock_ms
        or frame.period != event["period"]
        or frame.event_team_id != event["team"]["id"]
    ):
        raise ValueError("Historical 360 event alignment mismatch")
    return HistoricalReplayMoment(
        match_id=fixture.manifest.match_id,
        event_id=event_id,
        clock_ms=clock_ms,
        period=event["period"],
        event_sha256=frames.event_sha256,
        frame_sha256=frames.frame_sha256,
        frame=frame,
    )
