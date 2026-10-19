"""Provider-neutral player/ball contract: never invent tracking, rights or poses."""
import pytest
from pydantic import ValidationError

from pitchvolt.events import Point
from pitchvolt.tracking_contract import (
    CaptureMode,
    FileFingerprint,
    LocationStatus,
    ObservedLocation,
    PlayerObservation,
    PossessionObservation,
    PossessionState,
    SourceCoordinate,
    TrackingManifest,
    TrackingSequence,
    TrackingSnapshot,
    TrackingSource,
)

HASH = "a" * 64
COMMIT = "e706dd506b360d69d9d123d5b8026e7294b13996"


def fingerprint(kind):
    return FileFingerprint(
        source_kind=kind, sha256=HASH,
        source_url=f"https://github.com/metrica-sports/sample-data/blob/{COMMIT}/{kind}",
    )


def manifest(*, mode=CaptureMode.CONTINUOUS, provider=TrackingSource.METRICA_SAMPLE,
             fixture_id="metrica:game-1"):
    names = ("events", "home_tracking", "away_tracking") if mode == CaptureMode.CONTINUOUS else (
        "events", "freeze_frames",
    )
    return TrackingManifest(
        provider=provider, capture_mode=mode, fixture_id=fixture_id,
        match_id="sample-game-1", source_revision=COMMIT,
        files=tuple(fingerprint(kind) for kind in names),
    )


def position(*, x=0.5, y=0.5, units="normalized_0_1"):
    px = x * (105 if units == "normalized_0_1" else 105 / 120)
    py = y * (68 if units == "normalized_0_1" else 68 / 80)
    return ObservedLocation(
        status=LocationStatus.OBSERVED,
        raw=SourceCoordinate(x=x, y=y, units=units),
        pitch=Point(x=px, y=py),
    )


def missing():
    return ObservedLocation(status=LocationStatus.MISSING)


def snapshot(*, match_id="sample-game-1", clock=40, frame=1, period=1,
             event=None, players=(), ball=None, possession=None, record=None):
    return TrackingSnapshot(
        match_id=match_id,
        source_record_id=record or f"raw-{period}-{frame}-{clock}",
        period=period, clock_ms=clock,
        source_frame=frame, source_event_id=event,
        players=players, ball=missing() if ball is None else ball,
        possession=PossessionObservation() if possession is None else possession,
    )


def test_exact_sample_lookup_never_interpolates_while_ball_remains_unknown():
    p = PlayerObservation(
        detection_id="home-slot-11", player_id="11", team_id="home",
        location=position(),
    )
    first = snapshot(players=(p,), ball=missing())
    second = snapshot(clock=80, frame=2, players=(), ball=position())
    seq = TrackingSequence(manifest=manifest(), snapshots=(first, second))
    assert seq.at_exact_sample(1, 40) == first
    assert seq.at_exact_sample(1, 60) is None
    assert seq.at_exact_sample(1, 80) == second
    assert seq.at_exact_sample(2, 40) is None
    assert first.ball.pitch is None
    assert first.players[0].location.pitch == Point(x=52.5, y=34)
    assert second.players == ()
    assert seq.public_replay_enabled is False
    assert seq.manifest.serving_enabled is False


def test_event_exact_freeze_frame_requires_event_id_and_does_not_track_between_events():
    source = manifest(mode=CaptureMode.EVENT_EXACT, provider=TrackingSource.STATSBOMB_360)
    unknown_identity = PlayerObservation(
        detection_id="event1-detection-1",
        location=position(x=60.0, y=40.0, units="statsbomb_120x80"),
    )
    event1 = snapshot(event="event-1", frame=None, players=(unknown_identity,))
    seq = TrackingSequence(manifest=source, snapshots=(event1,))
    assert seq.at_event("event-1") == event1
    assert seq.at_event("event-2") is None
    assert seq.at_event("unknown") is None
    assert unknown_identity.player_id is None
    with pytest.raises(ValueError, match="exact event lookup"):
        seq.at_exact_sample(1, 40)
    with pytest.raises(ValueError, match="cannot invent source-event joins"):
        TrackingSequence(
            manifest=manifest(), snapshots=(snapshot(),)
        ).at_event("event-1")


@pytest.mark.parametrize("bad", [
    {"status": "missing", "raw": {"x": 0.5, "y": 0.5, "units": "normalized_0_1"}},
    {"status": "observed_on_pitch", "pitch": {"x": 52.5, "y": 34}},
    {"status": "observed_on_pitch", "raw": {"x": 0.5, "y": 0.5,
                                            "units": "normalized_0_1"}},
    {"status": "observed_on_pitch", "raw": {"x": 0.5, "y": 0.5,
                                            "units": "normalized_0_1"},
     "pitch": {"x": 75, "y": 34}},
    {"status": "observed_outside_pitch", "raw": {"x": 0.5, "y": 0.5,
                                                "units": "normalized_0_1"}},
    {"status": "observed_outside_pitch", "raw": {"x": -0.2, "y": 0.5,
                                                "units": "normalized_0_1"},
     "pitch": {"x": 0, "y": 34}},
])
def test_missing_and_nonobserved_locations_never_become_fake_pitch_positions(bad):
    with pytest.raises(ValidationError):
        ObservedLocation.model_validate(bad)


def test_real_off_pitch_coordinate_preserved_and_unrenderable():
    off = ObservedLocation(
        status=LocationStatus.OUTSIDE_PITCH,
        raw=SourceCoordinate(x=-0.02, y=0.5, units="normalized_0_1"),
    )
    assert off.pitch is None and off.raw.x == -0.02
    assert position(units="normalized_0_1").pitch == Point(x=52.5, y=34)
    assert position(x=120.0, y=80.0, units="statsbomb_120x80").pitch == Point(
        x=105, y=68,
    )


@pytest.mark.parametrize("mutate", [
    lambda d: d.update({"status": "observed_on_pitch"}),
    lambda d: d.update({"pitch": {"x": 52.5, "y": 34}}),
])
def test_explicitly_missing_ball_is_not_assignable_source_position(mutate):
    value = missing().model_dump(mode="json")
    mutate(value)
    with pytest.raises(ValidationError):
        ObservedLocation.model_validate(value)


def test_source_possession_requires_evidence_and_no_invented_contest_holder():
    reported = PossessionObservation(
        state=PossessionState.CONTROLLED, team_id="home",
        source_evidence_ids=("source-event-5",),
    )
    assert reported.player_id is None
    contested = PossessionObservation(
        state=PossessionState.CONTESTED, source_evidence_ids=("source-duel-1",),
    )
    assert contested.team_id is None
    for fields in [
        {"state": "unknown", "team_id": "home"},
        {"state": "source_reported_controlled", "team_id": "home"},
        {"state": "source_reported_contested", "player_id": "12",
         "team_id": "home", "source_evidence_ids": ("e1",)},
        {"state": "source_reported_controlled", "player_id": "12",
         "source_evidence_ids": ("e1",)},
        {"state": "source_reported_controlled", "team_id": "home",
         "source_evidence_ids": ("e1", "e1")},
    ]:
        with pytest.raises(ValidationError):
            PossessionObservation.model_validate(fields)


def test_manifest_must_prove_file_origin_without_granting_redistribution():
    original = manifest()
    assert original.rights_status == "unverified"
    assert original.serving_enabled is False
    with pytest.raises(ValidationError):
        TrackingManifest.model_validate(
            original.model_dump() | {"serving_enabled": True}
        )
    with pytest.raises(ValidationError, match="approval"):
        TrackingManifest(
            **(original.model_dump(exclude={"rights_status", "rights_evidence_url"})),
            rights_status="public_permission_documented",
        )
    acknowledged = TrackingManifest(
        **(original.model_dump(exclude={"rights_status", "rights_evidence_url"})),
        rights_status="approved_private_research",
        rights_evidence_url="https://example.org/permission-record",
    )
    assert acknowledged.serving_enabled is False
    with pytest.raises(ValidationError):
        TrackingManifest.model_validate(
            original.model_dump() | {"schema_version": 2}
        )


def test_provider_mode_file_contract_and_extra_fields_fail_closed():
    with pytest.raises(ValidationError, match="Metrica CSV"):
        manifest(mode=CaptureMode.EVENT_EXACT, provider=TrackingSource.METRICA_SAMPLE)
    with pytest.raises(ValidationError, match="StatsBomb 360"):
        manifest(mode=CaptureMode.CONTINUOUS, provider=TrackingSource.STATSBOMB_360)
    with pytest.raises(ValidationError):
        TrackingManifest.model_validate(manifest().model_dump() | {"unknown_key": "x"})
    with pytest.raises(ValidationError, match="Duplicate"):
        TrackingManifest.model_validate(
            manifest().model_dump() | {"files": [
                fingerprint("events").model_dump(), fingerprint("events").model_dump(),
            ]}
        )


def test_sequence_rejects_cross_match_reorder_duplicate_cursor_and_frames():
    first = snapshot()
    second = snapshot(frame=2, clock=80)
    original = manifest()
    for seq in [
        (first, snapshot(frame=2, clock=80, match_id="other-game")),
        (second, first),
        (first, snapshot(frame=2, clock=40)),
        (first, snapshot(frame=1, clock=80)),
    ]:
        with pytest.raises(ValidationError):
            TrackingSequence(manifest=original, snapshots=seq)
    with pytest.raises(ValidationError):
        TrackingSequence(manifest=original, snapshots=())


def test_identified_players_cannot_be_duplicated_or_assigned_unknown_teams():
    valid = PlayerObservation(
        detection_id="a", player_id="12", team_id="home", location=position(),
    )
    with pytest.raises(ValidationError, match="without verified team"):
        PlayerObservation(detection_id="x", player_id="12", location=position())
    with pytest.raises(ValidationError, match="Same identified player"):
        snapshot(players=(valid, PlayerObservation(
            detection_id="b", player_id="12", team_id="home", location=missing(),
        )))
    with pytest.raises(ValidationError, match="Duplicate player detection"):
        snapshot(players=(valid, PlayerObservation(
            detection_id="a", team_id="away", location=missing(),
        )))
    with pytest.raises(ValidationError, match="eleven"):
        snapshot(players=tuple(
            PlayerObservation(detection_id=str(i), team_id="home", location=missing())
            for i in range(12)
        ))


def test_sequence_serialization_roundtrip_preserves_null_provenance_and_flags():
    seq = TrackingSequence(manifest=manifest(), snapshots=(snapshot(),))
    wire = seq.model_dump(mode="json")
    assert wire["manifest"]["schema_version"] == 1
    assert wire["snapshots"][0]["ball"]["status"] == "missing"
    assert wire["snapshots"][0]["ball"]["raw"] is None
    assert wire["snapshots"][0]["ball"]["pitch"] is None
    assert TrackingSequence.model_validate(wire) == seq
    assert "synthetic" not in str(wire).lower()


def test_numeric_sample_keys_forbid_string_or_float_coercion():
    original = snapshot().model_dump()
    for key, bad in (("period", "1"), ("clock_ms", "40"), ("source_frame", 1.5)):
        with pytest.raises(ValidationError):
            TrackingSnapshot.model_validate(original | {key: bad})


def test_distinct_freeze_frames_can_share_an_exact_timestamp():
    """Two recorded events at the same clock must not be mistaken for motion."""
    frame1 = snapshot(frame=None, event="event-a", record="source-a")
    frame2 = snapshot(frame=None, event="event-b", record="source-b")
    seq = TrackingSequence(
        manifest=manifest(
            mode=CaptureMode.EVENT_EXACT,
            provider=TrackingSource.STATSBOMB_360,
        ),
        snapshots=(frame1, frame2),
    )
    assert seq.at_event("event-a") == frame1
    assert seq.at_event("event-b") == frame2
    with pytest.raises(ValidationError, match="Duplicate"):
        TrackingSequence(
            manifest=seq.manifest,
            snapshots=(frame1, snapshot(frame=None, event="event-a", record="source-b")),
        )
