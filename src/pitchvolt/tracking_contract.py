"""Versioned, provider-neutral *observed* football tracking contract.

No adapter, ingestion, HTTP endpoint, playback interpolation, or rights grant.
Historical tracking is NOT convertible to synthetic-only MatchEvent records.
This module only represents exact source-observed samples and missingness.
"""
from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pitchvolt.events import Point

# JSON payloads represent tuples as arrays and enums as strings; strict=True
# at model scope rejects valid wire-format roundtrips. Keep unknown fields
# forbidden and apply strict checks to the sensitive numeric sample keys.
STRICT = ConfigDict(frozen=True, extra="forbid")
SHA256 = r"^[0-9a-f]{64}$"
GIT_COMMIT = r"^[0-9a-f]{40}$"


class TrackingSource(StrEnum):
    METRICA_SAMPLE = "metrica_sample"
    STATSBOMB_360 = "statsbomb_360"
    LICENSED_OTHER = "licensed_other"


class CaptureMode(StrEnum):
    CONTINUOUS = "continuous_samples"
    EVENT_EXACT = "event_exact_freeze_frame"


class LocationStatus(StrEnum):
    OBSERVED = "observed_on_pitch"
    OUTSIDE_PITCH = "observed_outside_pitch"
    MISSING = "missing"


class PossessionState(StrEnum):
    UNKNOWN = "unknown"
    CONTROLLED = "source_reported_controlled"
    CONTESTED = "source_reported_contested"


class FileFingerprint(BaseModel):
    """Independently verified bytes; names identify exact provider inputs."""

    model_config = STRICT
    source_kind: Literal["events", "home_tracking", "away_tracking", "freeze_frames"]
    sha256: str = Field(pattern=SHA256)
    source_url: str = Field(min_length=1)
    git_blob_oid: str | None = Field(default=None, pattern=GIT_COMMIT)


class TrackingManifest(BaseModel):
    """Bounded immutable source identity; no license grant is inferred."""

    model_config = STRICT
    schema_version: Literal[1] = 1
    provider: TrackingSource
    capture_mode: CaptureMode
    match_id: str = Field(min_length=1)
    fixture_id: str = Field(min_length=1)
    source_revision: str = Field(min_length=7)
    files: tuple[FileFingerprint, ...] = Field(min_length=1)
    rights_status: Literal[
        "unverified", "approved_private_research", "public_permission_documented",
    ] = "unverified"
    rights_evidence_url: str | None = None
    # Independent approval is required before any hosted replay can be added.
    serving_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_source(self) -> TrackingManifest:
        kinds = [f.source_kind for f in self.files]
        if len(set(kinds)) != len(kinds):
            raise ValueError("Duplicate tracked source file type")
        if self.provider == TrackingSource.METRICA_SAMPLE:
            if self.capture_mode != CaptureMode.CONTINUOUS:
                raise ValueError("Metrica CSV is sampled tracking, not a freeze frame")
            if set(kinds) != {"events", "home_tracking", "away_tracking"}:
                raise ValueError("Metrica requires matched Home/Away/Events fingerprints")
            if not self.source_revision or not (
                len(self.source_revision) == 40
                and all(ch in "0123456789abcdef" for ch in self.source_revision)
            ):
                raise ValueError("Metrica requires immutable Git commit")
        if self.provider == TrackingSource.STATSBOMB_360:
            if self.capture_mode != CaptureMode.EVENT_EXACT:
                raise ValueError("StatsBomb 360 is event-local, not continuous")
            if set(kinds) != {"events", "freeze_frames"}:
                raise ValueError("360 requires event and frame fingerprints")
        if self.rights_status != "unverified" and not self.rights_evidence_url:
            raise ValueError("Explicit rights approval requires a source evidence URL")
        if self.rights_status == "unverified" and self.rights_evidence_url is not None:
            raise ValueError("Unverified rights must not carry an approval assertion")
        return self


class SourceCoordinate(BaseModel):
    """Native provider coordinate; off-pitch values are preserved, not clamped."""

    model_config = STRICT
    x: float = Field(allow_inf_nan=False)
    y: float = Field(allow_inf_nan=False)
    units: Literal["normalized_0_1", "statsbomb_120x80", "pitch_meters"]


def _canonical_position(raw: SourceCoordinate) -> tuple[float, float]:
    """One auditable source->105x68 conversion; no rounding or clamping."""
    if raw.units == "normalized_0_1":
        return raw.x * 105, raw.y * 68
    if raw.units == "statsbomb_120x80":
        return raw.x * (105 / 120), raw.y * (68 / 80)
    return raw.x, raw.y


class ObservedLocation(BaseModel):
    """Exactly one of observed, off-field, or explicitly unknown."""

    model_config = STRICT
    status: LocationStatus
    raw: SourceCoordinate | None = None
    pitch: Point | None = None

    @model_validator(mode="after")
    def validate_coverage(self) -> ObservedLocation:
        if self.status == LocationStatus.MISSING:
            if self.raw is not None or self.pitch is not None:
                raise ValueError("Missing sample cannot have synthetic coordinates")
        elif self.status == LocationStatus.OUTSIDE_PITCH:
            if self.raw is None or self.pitch is not None:
                raise ValueError("Outside-pitch source data cannot be clamped to pitch")
            x, y = _canonical_position(self.raw)
            if 0 <= x <= 105 and 0 <= y <= 68:
                raise ValueError("Inside-field source point cannot be labelled off-pitch")
        else:
            if self.raw is None or self.pitch is None:
                raise ValueError("Observed on-pitch sample requires source and pitch coordinates")
            x, y = _canonical_position(self.raw)
            if not (
                # The pre-existing StatsBomb normalizer outputs six
                # decimal places; tolerate ONLY its <=0.5 micrometre
                # rounding while rejecting a changed source position.
                math.isclose(x, self.pitch.x, rel_tol=0, abs_tol=5.1e-7)
                and math.isclose(y, self.pitch.y, rel_tol=0, abs_tol=5.1e-7)
            ):
                raise ValueError("Pitch coordinate differs from recorded source position")
        return self


class PlayerObservation(BaseModel):
    model_config = STRICT
    detection_id: str = Field(min_length=1)
    # Anonymous observations must remain anonymous across frames.
    player_id: str | None = None
    team_id: str | None = None
    location: ObservedLocation
    keeper: bool | None = None

    @model_validator(mode="after")
    def identifiable_player(self) -> PlayerObservation:
        if self.player_id == "" or self.team_id == "":
            raise ValueError("Empty player/team identity")
        if self.player_id is not None and self.team_id is None:
            raise ValueError("Player ID without verified team identity")
        return self


class PossessionObservation(BaseModel):
    """Source-reported semantic fact, never inferred from spatial proximity."""

    model_config = STRICT
    state: PossessionState = PossessionState.UNKNOWN
    team_id: str | None = None
    player_id: str | None = None
    source_evidence_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def provenance_for_possession(self) -> PossessionObservation:
        if self.state == PossessionState.UNKNOWN:
            if self.team_id or self.player_id or self.source_evidence_ids:
                raise ValueError("Unknown possession must not claim a controlling entity")
        else:
            if not self.source_evidence_ids or any(not i for i in self.source_evidence_ids):
                raise ValueError("Reported possession/contest needs source evidence")
            if len(self.source_evidence_ids) != len(set(self.source_evidence_ids)):
                raise ValueError("Duplicate possession evidence IDs")
            if self.state == PossessionState.CONTROLLED and not self.team_id:
                raise ValueError("Reported control requires source team identity")
            if self.state == PossessionState.CONTESTED and self.player_id is not None:
                raise ValueError("Contested state cannot invent a ball carrier")
            if self.player_id is not None and self.team_id is None:
                raise ValueError("Ball carrier must have a known team")
        return self


class TrackingSnapshot(BaseModel):
    """One exact historical source sample, never interpolated or forward-filled."""

    model_config = STRICT
    match_id: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    period: int = Field(ge=1, le=4, strict=True)
    clock_ms: int = Field(ge=0, strict=True)
    # Event-exact frames require event_id. Continuous samples require a frame.
    source_event_id: str | None = None
    source_frame: int | None = Field(default=None, ge=0, strict=True)
    players: tuple[PlayerObservation, ...] = Field(max_length=22)
    ball: ObservedLocation
    possession: PossessionObservation = Field(default_factory=PossessionObservation)

    @model_validator(mode="after")
    def unique_observations(self) -> TrackingSnapshot:
        detections = [p.detection_id for p in self.players]
        if len(detections) != len(set(detections)):
            raise ValueError("Duplicate player detection in a single snapshot")
        identities = [(p.team_id, p.player_id) for p in self.players if p.player_id]
        if len(identities) != len(set(identities)):
            raise ValueError("Same identified player observed twice")
        teams = {p.team_id for p in self.players if p.team_id}
        if any(sum(p.team_id == team for p in self.players) > 11 for team in teams):
            raise ValueError("More than eleven observed players on one team")
        if self.source_event_id == "":
            raise ValueError("Empty source event identity")
        return self


class TrackingSequence(BaseModel):
    """No interpolation: select exactly one source frame/event or return None."""

    model_config = STRICT
    manifest: TrackingManifest
    snapshots: tuple[TrackingSnapshot, ...] = Field(min_length=1)
    # Representation alone never authorizes public streaming or hosting.
    public_replay_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_sequence(self) -> TrackingSequence:
        mode = self.manifest.capture_mode
        seen_records: set[str] = set()
        seen_cursor: set[tuple[int, int]] = set()
        seen_events: set[str] = set()
        previous: tuple[int, int] | None = None
        previous_frame: int | None = None
        for frame in self.snapshots:
            if frame.match_id != self.manifest.match_id:
                raise ValueError("Tracking snapshot cross-match identity mismatch")
            key = (frame.period, frame.clock_ms)
            if frame.source_record_id in seen_records or (
                mode == CaptureMode.CONTINUOUS and key in seen_cursor
            ):
                raise ValueError("Duplicate tracking record or exact sample cursor")
            if previous is not None and (
                key < previous or (mode == CaptureMode.CONTINUOUS and key == previous)
            ):
                raise ValueError("Tracking snapshots must be time-ordered")
            if mode == CaptureMode.CONTINUOUS:
                if frame.source_frame is None or frame.source_event_id is not None:
                    raise ValueError("Continuous snapshots require frame, not event frame")
                if (previous_frame is not None and previous is not None
                    and frame.period == previous[0]
                    and frame.source_frame <= previous_frame):
                    raise ValueError("Continuous source frame must advance within period")
                previous_frame = frame.source_frame
            else:
                if frame.source_event_id is None or frame.source_frame is not None:
                    raise ValueError("Freeze frames require exact event ID, not frame index")
                if frame.source_event_id in seen_events:
                    raise ValueError("Duplicate source event freeze frame")
                seen_events.add(frame.source_event_id)
            seen_records.add(frame.source_record_id)
            seen_cursor.add(key)
            previous = key
        return self

    def at_exact_sample(self, period: int, clock_ms: int) -> TrackingSnapshot | None:
        """Only tracking frames support time lookup. Never seek nearest."""
        if self.manifest.capture_mode != CaptureMode.CONTINUOUS:
            raise ValueError("Event-local freeze frames require exact event lookup")
        return next(
            (s for s in self.snapshots if (s.period, s.clock_ms) == (period, clock_ms)),
            None,
        )

    def at_event(self, source_event_id: str) -> TrackingSnapshot | None:
        """Only event-local freeze frames support source UUID lookup."""
        if self.manifest.capture_mode != CaptureMode.EVENT_EXACT:
            raise ValueError("Continuous tracking cannot invent source-event joins")
        return next((s for s in self.snapshots if s.source_event_id == source_event_id), None)
