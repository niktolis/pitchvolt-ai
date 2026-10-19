"""Offline StatsBomb 360 projection tests: original synthetic JSON, no source bytes."""
from dataclasses import replace
import hashlib
import json

import pytest
from pydantic import ValidationError

from pitchvolt.fixture_manifest import FixtureManifest, FixtureOrigin
from pitchvolt.providers.statsbomb_360 import load_historical_360
from pitchvolt.providers.statsbomb_360_tracking import project_360_tracking
from pitchvolt.providers.statsbomb_historical import load_historical_fixture
from pitchvolt.tracking_contract import CaptureMode, LocationStatus, PossessionState

MATCH = "3764440"
REVISION = "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"
EVENT_URL = (
    f"https://github.com/hudl/open-data/blob/{REVISION}/data/events/{MATCH}.json"
)
FRAME_URL = (
    f"https://github.com/hudl/open-data/blob/{REVISION}/data/three-sixty/{MATCH}.json"
)


def _records(*, same_clock=False):
    return [
        {
            "id": "source-a", "index": 1, "period": 1,
            "minute": 0, "second": 1, "timestamp": "00:00:01.250",
            "team": {"id": 20}, "player": {"id": 99},
            "type": {"name": "Pass"},
        },
        {
            "id": "source-b", "index": 2, "period": 1,
            "minute": 0, "second": 1 if same_clock else 2,
            "timestamp": "00:00:01.250" if same_clock else "00:00:02.000",
            "team": {"id": 30}, "player": {"id": 101},
            "type": {"name": "Carry"},
        },
    ]


def _frames(*, include_second=False, off_pitch=True):
    player = [
        {"teammate": True, "actor": True, "keeper": False, "location": [120, 80]},
        {"teammate": False, "actor": False, "keeper": True,
         "location": [121, -1] if off_pitch else [0, 0]},
        {"teammate": True, "actor": False, "keeper": False, "location": [60, 40]},
    ]
    entries = [
        {
            "event_uuid": "source-a",
            "visible_area": [0, 0, 120, 0, 120, 80, 0, 80],
            "freeze_frame": player,
        },
    ]
    if include_second:
        entries.append({
            "event_uuid": "source-b",
            "visible_area": [0, 0, 120, 0, 120, 80, 0, 80],
            "freeze_frame": [],
        })
    return entries


def _load(tmp_path, *, records=None, frames=None):
    events = _records() if records is None else records
    frame_data = _frames() if frames is None else frames
    event_bytes = json.dumps(events).encode("utf-8")
    event_file = tmp_path / f"{MATCH}.json"
    event_file.write_bytes(event_bytes)
    manifest = FixtureManifest(
        fixture_id="statsbomb:historical-fixture",
        origin=FixtureOrigin.STATSBOMB_OPEN_DATA,
        match_id=MATCH,
        event_sha256=hashlib.sha256(event_bytes).hexdigest(),
        event_count=len(events),
        match_duration_ms=5_400_000,
        event_coverage="excerpt",
        source_url=EVENT_URL,
        attribution="StatsBomb Open Data",
    )
    fixture = load_historical_fixture(event_file, manifest)
    frame_bytes = json.dumps(frame_data).encode("utf-8")
    frame_file = tmp_path / f"{MATCH}.360.json"
    frame_file.write_bytes(frame_bytes)
    bundle = load_historical_360(
        frame_file, fixture, expected_sha256=hashlib.sha256(frame_bytes).hexdigest(),
    )
    return fixture, bundle


def _project(fixture, bundle, *, url=FRAME_URL):
    return project_360_tracking(fixture, bundle, frame_source_url=url)


def test_real_loaders_project_source_exact_observations_and_unknown_ball(tmp_path):
    fixture, bundle = _load(tmp_path)
    projection = _project(fixture, bundle)
    assert projection.manifest.provider.value == "statsbomb_360"
    assert projection.manifest.capture_mode == CaptureMode.EVENT_EXACT
    assert projection.manifest.source_revision == REVISION
    assert projection.manifest.files[0].sha256 == fixture.manifest.event_sha256
    assert projection.manifest.files[1].sha256 == bundle.frame_sha256
    assert projection.manifest.rights_status == "unverified"
    assert projection.manifest.serving_enabled is False
    assert projection.public_replay_enabled is False

    snap = projection.at_event("source-a")
    assert snap is not None
    assert snap.match_id == MATCH
    assert snap.source_record_id == "statsbomb360:source-a"
    assert snap.period == 1 and snap.clock_ms == 1250
    assert snap.source_frame is None
    assert len(snap.players) == 3
    actor, opponent, anonymous_teammate = snap.players
    assert actor.player_id == "99"
    assert actor.team_id == "20"
    assert actor.location.pitch.x == 105 and actor.location.pitch.y == 68
    assert actor.location.raw.x == 120
    assert opponent.player_id is None and opponent.team_id is None
    assert opponent.keeper is True
    assert opponent.location.status == LocationStatus.OUTSIDE_PITCH
    assert opponent.location.raw.x == 121
    assert opponent.location.pitch is None
    assert anonymous_teammate.player_id is None
    assert anonymous_teammate.team_id == "20"
    assert anonymous_teammate.location.pitch.x == 52.5
    assert anonymous_teammate.location.pitch.y == 34
    assert snap.ball.status == LocationStatus.MISSING
    assert snap.ball.raw is None and snap.ball.pitch is None
    assert snap.possession.state == PossessionState.UNKNOWN
    assert snap.possession.team_id is None and snap.possession.player_id is None


def test_no_nearest_frame_or_actor_carry_forward(tmp_path):
    fixture, bundle = _load(tmp_path)
    result = _project(fixture, bundle)
    assert result.at_event("source-a") is not None
    assert result.at_event("source-b") is None
    assert result.at_event("future-event") is None
    with pytest.raises(ValueError, match="exact event lookup"):
        result.at_exact_sample(1, 1250)


def test_same_clock_distinct_events_remain_distinct_and_empty_camera_stays_empty(tmp_path):
    fixture, bundle = _load(
        tmp_path, records=_records(same_clock=True),
        frames=_frames(include_second=True),
    )
    projected = _project(fixture, bundle)
    assert len(projected.snapshots) == 2
    assert projected.at_event("source-a").clock_ms == 1250
    second = projected.at_event("source-b")
    assert second is not None and second.clock_ms == 1250
    assert second.players == ()
    assert second.ball.status == LocationStatus.MISSING
    assert second.possession.state == PossessionState.UNKNOWN


@pytest.mark.parametrize("url", [
    "https://github.com/hudl/open-data/blob/master/data/three-sixty/3764440.json",
    f"https://github.com/hudl/open-data/blob/{REVISION}/data/three-sixty/other.json",
    "https://example.org/fake-360.json",
])
def test_frame_url_requires_same_pinned_revision_match(tmp_path, url):
    fixture, bundle = _load(tmp_path)
    with pytest.raises(ValueError, match="source URL"):
        _project(fixture, bundle, url=url)


def test_fixture_url_must_be_immutable_and_match_specific(tmp_path):
    fixture, bundle = _load(tmp_path)
    manifest = fixture.manifest.model_copy(update={
        "source_url": "https://github.com/hudl/open-data/blob/master/data/events/3764440.json",
    })
    with pytest.raises(ValueError, match="immutable source revision"):
        _project(replace(fixture, manifest=manifest), bundle)
    wrong = fixture.manifest.model_copy(update={
        "source_url": EVENT_URL.replace("3764440.json", "not-this-game.json"),
    })
    with pytest.raises(ValueError, match="immutable source revision"):
        _project(replace(fixture, manifest=wrong), bundle)


def test_rejects_cross_match_origin_hash_time_team_and_missing_event(tmp_path):
    fixture, bundle = _load(tmp_path)
    origin = fixture.manifest.model_copy(update={
        "origin": FixtureOrigin.PITCHVOLT_SYNTHETIC,
    })
    with pytest.raises(ValueError, match="synthetic fixture"):
        _project(replace(fixture, manifest=origin), bundle)
    with pytest.raises(ValueError, match="cross-match"):
        _project(fixture, replace(bundle, match_id="different"))
    with pytest.raises(ValueError, match="source event hash"):
        _project(fixture, replace(bundle, event_sha256="f" * 64))
    frame = bundle.frames[0]
    for bad in [
        replace(frame, clock_ms=1300),
        replace(frame, period=2),
        replace(frame, event_team_id=30),
    ]:
        with pytest.raises(ValueError, match="alignment"):
            _project(fixture, replace(bundle, frames=(bad,)))
    with pytest.raises(ValueError, match="absent from fixture"):
        _project(fixture, replace(bundle, frames=(replace(frame, event_id="wrong"),)))


def test_rejects_unbacked_identity_or_tampered_source_coordinates(tmp_path):
    fixture, bundle = _load(tmp_path)
    frame = bundle.frames[0]
    actor = frame.observations[0]
    for bad in [
        replace(actor, actor=False),  # ID is only known for original event actor
        replace(actor, observation_index=10),
        replace(actor, teammate=False),
    ]:
        changed = replace(frame, observations=(bad, *frame.observations[1:]))
        with pytest.raises((ValueError, ValidationError)):
            _project(fixture, replace(bundle, frames=(changed,)))
    # A preprojected pitch position must actually derive from source location.
    changed = replace(actor, source_location=(40, 30))
    frame_with_fake_pitch = replace(frame, observations=(changed, *frame.observations[1:]))
    with pytest.raises(ValidationError, match="Pitch coordinate differs"):
        _project(fixture, replace(bundle, frames=(frame_with_fake_pitch,)))


def test_duplicate_freeze_frame_is_rejected_not_collapsed(tmp_path):
    fixture, bundle = _load(tmp_path)
    with pytest.raises(ValidationError, match="Duplicate"):
        _project(fixture, replace(bundle, frames=(bundle.frames[0], bundle.frames[0])))


def test_no_implicit_network_or_public_api_in_projection(tmp_path, monkeypatch):
    fixture, bundle = _load(tmp_path)

    def no_http(*args, **kwargs):
        raise AssertionError("Source adapter cannot initiate HTTP")

    monkeypatch.setattr("urllib.request.urlopen", no_http)
    assert _project(fixture, bundle).public_replay_enabled is False
