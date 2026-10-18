"""Provider-neutral *replay presentation* boundary with explicit source provenance.

This is not a common tactical/event schema: real historical actions must NEVER
be converted to synthetic-only MatchEvent or fed into MatchProcessor. The
dataset presents verified, source-event-exact actor observations to future
replay transports and browser consumers without inventing tracking.
"""
from __future__ import annotations

import hashlib
from bisect import bisect_right
from dataclasses import dataclass, field
from typing import Protocol

from pitchvolt.events import MatchEvent, MatchMetadata, Point, validate_stream
from pitchvolt.extended_fixtures import EXTENDED_SCENARIO
from pitchvolt.fixture_manifest import FixtureManifest, FixtureOrigin
from pitchvolt.providers.statsbomb_historical import HistoricalFixture
from pitchvolt.providers.statsbomb_projection import project_historical_actions
from pitchvolt.scenarios import SCENARIO_NAMES, scenario


@dataclass(frozen=True)
class ReplayAction:
    """Observed original action at ONE source event time, not player tracking."""

    event_id: str
    source_index: int
    period: int
    clock_ms: int
    kind: str
    location: Point
    destination: Point | None
    team_id: str | None
    player_id: str | None
    team_label: str | None = None
    player_label: str | None = None


@dataclass(frozen=True)
class ReplayCursorSnapshot:
    """The latest *reported event*, never an interpolated location at the cursor."""

    cursor_ms: int
    latest_event: ReplayAction | None
    visible_action_count: int
    observation_at_cursor: bool


@dataclass(frozen=True)
class ReplayDataset:
    """Unified query surface, but deliberately distinct provenance/capabilities.

    `manifest.event_count` describes the ORIGINAL input, whereas `actions`
    may omit historical action families. Only synthetic datasets carry valid
    canonical MatchEvent values usable by the deterministic intelligence core.
    """

    manifest: FixtureManifest
    actions: tuple[ReplayAction, ...]
    canonical_match: MatchMetadata | None = None
    canonical_events: tuple[MatchEvent, ...] = ()
    omitted_by_type: tuple[tuple[str, int], ...] = ()
    _clock_index: tuple[int, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        synthetic = self.manifest.origin == FixtureOrigin.PITCHVOLT_SYNTHETIC
        if synthetic != (self.canonical_match is not None):
            raise ValueError("Canonical match state is available only for synthetic replay")
        if synthetic and (
            len(self.canonical_events) != self.manifest.event_count
            or len(self.actions) != len(self.canonical_events)
            or self.canonical_match is None
            or self.canonical_match.match_id != self.manifest.match_id
        ):
            raise ValueError("Synthetic replay must retain all original canonical events")
        if not synthetic and self.canonical_events:
            raise ValueError("Historical replay must not fabricate synthetic canonical events")
        if len(self.actions) > self.manifest.event_count:
            raise ValueError("Replay projection has more actions than original events")
        if any(n <= 0 for _, n in self.omitted_by_type):
            raise ValueError("Omission counts must be positive")
        prior: tuple[int, int, int] | None = None
        ids: set[str] = set()
        for action in self.actions:
            if not action.event_id or action.event_id in ids or action.source_index < 1:
                raise ValueError("Duplicate, empty or invalid replay source event identity")
            key = (action.period, action.clock_ms, action.source_index)
            if (\n                action.period < 1 or action.clock_ms < 0\n                or (prior is not None and key <= prior)\n                or (prior is not None and action.clock_ms < prior[1])\n            ):
                raise ValueError("Replay events must be ordered by period, clock and source index")
            if synthetic and (not action.team_id or not action.player_id):
                raise ValueError("Synthetic replay is missing canonical actor identity")
            if not synthetic and (action.team_id is not None or action.player_id is not None):
                raise ValueError("Historical display names are not verified canonical IDs")
            ids.add(action.event_id)
            prior = key
        object.__setattr__(self, "_clock_index", tuple(a.clock_ms for a in self.actions))

    @property
    def origin(self) -> FixtureOrigin:
        return self.manifest.origin

    @property
    def permits_tactical_processing(self) -> bool:
        return self.canonical_match is not None

    @property
    def projected_count(self) -> int:
        return len(self.actions)

    def at_cursor(self, cursor_ms: int) -> ReplayCursorSnapshot:
        """Binary-search past events; never claim a carried event actor is current.

        No samples exist before the first source action. A later action at the
        same cursor timestamp is selected by its original source index.
        """
        if not isinstance(cursor_ms, int) or cursor_ms < 0:
            raise ValueError("Replay cursor must be a nonnegative integer millisecond clock")
        count = bisect_right(self._clock_index, cursor_ms)
        latest = self.actions[count - 1] if count else None
        return ReplayCursorSnapshot(
            cursor_ms=cursor_ms,
            latest_event=latest,
            visible_action_count=count,
            observation_at_cursor=latest is not None and latest.clock_ms == cursor_ms,
        )


class ReplaySource(Protocol):
    """Small loader interface; source validation remains in existing adapters."""

    def load(self) -> ReplayDataset: ...


@dataclass(frozen=True)
class SyntheticReplaySource:
    name: str
    seed: int = 42

    def load(self) -> ReplayDataset:
        if self.name not in SCENARIO_NAMES:
            raise ValueError("Unknown synthetic replay scenario")
        match, events = scenario(self.name, self.seed)
        validate_stream(events, match)
        digest = hashlib.sha256(
            b"".join(event.model_dump_json().encode("utf-8") + b"\n" for event in events)
        ).hexdigest()
        # Only the deliberately full-clock extended synthetic fixture claims
        # regulation-time coverage; legacy six-event scenarios are excerpts.
        full_clock = (
            self.name == EXTENDED_SCENARIO and events[0].clock_ms == 0
            and events[-1].clock_ms == 5_400_000
        )
        manifest = FixtureManifest(
            fixture_id=f"pitchvolt:{self.name}:{self.seed}",
            origin=FixtureOrigin.PITCHVOLT_SYNTHETIC,
            match_id=match.match_id,
            event_sha256=digest,
            event_count=len(events),
            match_duration_ms=max(1, events[-1].clock_ms),
            event_coverage="full_match" if full_clock else "excerpt",
            generator_seed=self.seed,
        )
        return ReplayDataset(
            manifest=manifest,
            actions=tuple(
                ReplayAction(
                    event_id=event.event_id,
                    source_index=event.sequence,
                    period=event.period,
                    clock_ms=event.clock_ms,
                    kind=event.event_type.value,
                    location=event.location,
                    destination=event.destination,
                    team_id=event.team_id,
                    player_id=event.player_id,
                ) for event in events
            ),
            canonical_match=match,
            canonical_events=tuple(events),
        )


@dataclass(frozen=True)
class HistoricalReplaySource:
    """Offline only; requires an independently SHA-checked original fixture."""

    fixture: HistoricalFixture

    def load(self) -> ReplayDataset:
        if self.fixture.manifest.origin != FixtureOrigin.STATSBOMB_OPEN_DATA:
            raise ValueError("Historical replay requires StatsBomb Open Data origin")
        projection = project_historical_actions(self.fixture)
        return ReplayDataset(
            manifest=self.fixture.manifest,
            actions=tuple(
                ReplayAction(
                    event_id=action.event_id,
                    source_index=action.index,
                    period=action.period,
                    clock_ms=action.clock_ms,
                    kind=action.kind,
                    location=Point(x=action.location_x, y=action.location_y),
                    destination=(
                        Point(x=action.destination_x, y=action.destination_y)
                        if action.destination_x is not None and action.destination_y is not None
                        else None
                    ),
                    # A historical player NAME is not a canonical synthetic ID.
                    team_id=None,
                    player_id=None,
                    team_label=action.team,
                    player_label=action.player,
                ) for action in projection.actions
            ),
            omitted_by_type=tuple(sorted(projection.omitted_by_type.items())),
        )
