"""Offline, event-exact StatsBomb 360 -> provider-neutral observation contract.

This is a strict projection of separately SHA-checked *local* source inputs.
No HTTP, historical stream API, player motion interpolation, cloud uploads,
original footage or redistribution authorization is supplied by this module.
"""
from __future__ import annotations

import re

from pitchvolt.fixture_manifest import FixtureOrigin
from pitchvolt.providers.statsbomb_360 import Historical360Bundle, Observed360Player
from pitchvolt.providers.statsbomb_historical import HistoricalFixture
from pitchvolt.providers.statsbomb_projection import historical_clock_ms
from pitchvolt.tracking_contract import (
    CaptureMode,
    FileFingerprint,
    LocationStatus,
    ObservedLocation,
    PlayerObservation,
    SourceCoordinate,
    TrackingManifest,
    TrackingSequence,
    TrackingSnapshot,
    TrackingSource,
)

_PINNED_EVENT_URL = re.compile(
    r"https://github\.com/hudl/open-data/blob/([0-9a-f]{40})/data/events/([0-9]+)\.json\Z"
)


def _observation(
    source: Observed360Player,
    *,
    event_id: str,
    event_team_id: int,
    expected_index: int,
) -> PlayerObservation:
    """A camera detection is NOT a persistent roster identity."""
    if source.observation_index != expected_index:
        raise ValueError("StatsBomb 360 detection index mismatch")
    if source.actor and not source.teammate:
        raise ValueError("StatsBomb 360 event actor must be a teammate")
    if source.player_id is not None and not source.actor:
        raise ValueError("Only the original event actor can have a source player ID")
    raw = SourceCoordinate(
        x=source.source_location[0],
        y=source.source_location[1],
        units="statsbomb_120x80",
    )
    location = ObservedLocation(
        status=(
            LocationStatus.OBSERVED if source.position is not None
            else LocationStatus.OUTSIDE_PITCH
        ),
        raw=raw,
        pitch=source.position,
    )
    return PlayerObservation(
        # Unique detection ID is scoped to one source event, not another frame.
        detection_id=f"{event_id}:camera-detection:{source.observation_index}",
        team_id=str(event_team_id) if source.teammate else None,
        player_id=str(source.player_id) if source.player_id is not None else None,
        location=location,
        keeper=source.keeper,
    )


def project_360_tracking(
    fixture: HistoricalFixture,
    frames: Historical360Bundle,
    *,
    frame_source_url: str,
) -> TrackingSequence:
    """Map verified historical 360 event freezes to tracking v1 without invention.

    The caller must have loaded both original files with the existing
    SHA-checked load_historical_fixture() and load_historical_360() loaders.
    A syntactically pinned source URL is not itself a fresh remote fetch or
    independent license verification. There is NO public playback capability.
    """
    if fixture.manifest.origin != FixtureOrigin.STATSBOMB_OPEN_DATA:
        raise ValueError("360 projection rejects synthetic fixture origin")
    if frames.match_id != fixture.manifest.match_id:
        raise ValueError("360 projection cross-match identity mismatch")
    if frames.event_sha256 != fixture.manifest.event_sha256:
        raise ValueError("360 projection source event hash mismatch")
    source_url = fixture.manifest.source_url
    pinned = _PINNED_EVENT_URL.fullmatch(source_url or "")
    if pinned is None or pinned.group(2) != fixture.manifest.match_id:
        raise ValueError("360 projection requires immutable source revision and match URL")
    revision = pinned.group(1)
    expected_frames_url = (
        f"https://github.com/hudl/open-data/blob/{revision}/data/"
        f"three-sixty/{fixture.manifest.match_id}.json"
    )
    if frame_source_url != expected_frames_url:
        raise ValueError("360 source URL/revision/match mismatch")
    if not frames.frames:
        raise ValueError("No verified source 360 frames to project")

    by_id = {record["id"]: record for record in fixture.records}
    if len(by_id) != len(fixture.records):
        raise ValueError("Duplicate original source event identity")

    ordered: list[tuple[int, int, int, TrackingSnapshot]] = []
    for frame in frames.frames:
        record = by_id.get(frame.event_id)
        if record is None:
            raise ValueError("360 frame source event absent from fixture")
        team = record.get("team")
        if not isinstance(team, dict) or type(team.get("id")) is not int:
            raise ValueError("360 original event missing team identity")
        if (
            frame.period != record["period"]
            or frame.clock_ms != historical_clock_ms(record)
            or frame.event_team_id != team["id"]
        ):
            raise ValueError("360 event time/period/team source alignment mismatch")

        # 360 has no independent sampled ball or player-carrier/duel evidence.
        # Existing 360 teammates/opponents give no persistent opponent IDs.
        players = tuple(
            _observation(
                item,
                event_id=frame.event_id,
                event_team_id=frame.event_team_id,
                expected_index=index,
            )
            for index, item in enumerate(frame.observations)
        )
        snap = TrackingSnapshot(
            match_id=fixture.manifest.match_id,
            source_record_id=f"statsbomb360:{frame.event_id}",
            source_event_id=frame.event_id,
            period=frame.period,
            clock_ms=frame.clock_ms,
            players=players,
            ball=ObservedLocation(status=LocationStatus.MISSING),
        )
        ordered.append((frame.period, frame.clock_ms, record["index"], snap))
    ordered.sort(key=lambda row: row[:3])

    manifest = TrackingManifest(
        provider=TrackingSource.STATSBOMB_360,
        capture_mode=CaptureMode.EVENT_EXACT,
        match_id=fixture.manifest.match_id,
        fixture_id=fixture.manifest.fixture_id,
        source_revision=revision,
        files=(
            FileFingerprint(
                source_kind="events",
                sha256=fixture.manifest.event_sha256,
                source_url=source_url,
            ),
            FileFingerprint(
                source_kind="freeze_frames",
                sha256=frames.frame_sha256,
                source_url=frame_source_url,
            ),
        ),
        rights_status="unverified",
        serving_enabled=False,
    )
    return TrackingSequence(
        manifest=manifest,
        snapshots=tuple(row[3] for row in ordered),
        public_replay_enabled=False,
    )
