"""Only hash-verified, exact-event 360 observations may be published."""

import hashlib
import json

import pytest

from matchpulse.fixture_manifest import FixtureManifest, FixtureOrigin
from matchpulse.providers.statsbomb_360 import load_historical_360
from matchpulse.providers.statsbomb_historical import HistoricalFixture


def fixture():
    records = [
        {"id": "source-action-1", "index": 1, "period": 1,
         "minute": 0, "second": 1, "timestamp": "00:00:01.250",
         "team": {"id": 20}, "player": {"id": 99}, "type": {"name": "Pass"}},
        {"id": "source-action-2", "index": 2, "period": 1,
         "minute": 0, "second": 2, "timestamp": "00:00:02.000",
         "team": {"id": 30}, "player": {"id": 100}, "type": {"name": "Carry"}},
    ]
    manifest = FixtureManifest(
        fixture_id="historical-demo", match_id="3764440",
        origin=FixtureOrigin.STATSBOMB_OPEN_DATA, event_sha256="e" * 64,
        event_count=len(records), match_duration_ms=5_400_000,
        event_coverage="excerpt",
        source_url="https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/data/events/3764440.json",
        attribution="StatsBomb Open Data",
    )
    return HistoricalFixture(
        manifest=manifest, records=tuple(records),
        event_counts={}, supported_count=0, presentation_count=0, unreviewed_count=0,
    )


def observation(*, teammate=True, actor=False, keeper=False, loc=None):
    return {"teammate": teammate, "actor": actor, "keeper": keeper,
            "location": [60, 40] if loc is None else loc}


def sample(players=None):
    return [{"event_uuid": "source-action-1",
             "visible_area": [0, 0, 120, 0, 120, 80, 0, 80],
             "freeze_frame": players if players is not None else [
                 observation(actor=True, loc=[120, 80]),
                 observation(teammate=False, keeper=True, loc=[0, 0]),
                 observation(),
             ]}]


def load(tmp_path, frames, *, fixture_override=None, sha_override=None):
    payload = json.dumps(frames).encode()
    path = tmp_path / "3764440.360.json"
    path.write_bytes(payload)
    return load_historical_360(
        path, fixture() if fixture_override is None else fixture_override,
        expected_sha256=sha_override or hashlib.sha256(payload).hexdigest(),
    )


def test_source_linked_positions_without_fabricated_roster(tmp_path):
    bundle = load(tmp_path, sample())
    frame = bundle.at_event("source-action-1")
    assert frame is not None
    assert bundle.event_sha256 == "e" * 64
    assert frame.event_team_id == 20
    assert frame.clock_ms == 1250
    assert len(frame.observations) == 3
    assert not frame.has_observed_full_xi
    assert frame.observations[0].player_id == 99
    assert (frame.observations[0].position.x, frame.observations[0].position.y) == (105, 68)
    assert frame.observations[1].player_id is None
    assert (frame.observations[1].position.x, frame.observations[1].position.y) == (0, 0)
    assert frame.observations[2].player_id is None
    assert bundle.at_event("source-action-2") is None
    assert bundle.at_event("unknown") is None


def test_exact_twenty_two_requires_eleven_on_each_side(tmp_path):
    positions = [observation(actor=i == 0, loc=[i + 1, 10]) for i in range(11)]
    positions += [observation(teammate=False, loc=[i + 31, 50]) for i in range(11)]
    frame = load(tmp_path, sample(positions)).frames[0]
    assert frame.has_observed_full_xi
    assert len({id(p) for p in frame.observations}) == 22
    assert sum(p.player_id is not None for p in frame.observations) == 1
    partial = load(tmp_path, sample(positions[:-1])).frames[0]
    assert not partial.has_observed_full_xi
    assert len(partial.observations) == 21


@pytest.mark.parametrize(("mutate", "error"), [
    (lambda a: a.update({"event_uuid": "not-in-events"}), "absent"),
    (lambda a: a.update({"visible_area": [1, 2, 3]}), "polygon"),
    (lambda a: a["freeze_frame"].append(observation(actor=True)), "Multiple"),
    (lambda a: a["freeze_frame"][0].update({"teammate": False}), "event team"),
    (lambda a: a["freeze_frame"][0].update({"keeper": 1}), "boolean"),
    (lambda a: a["freeze_frame"][0].update({"location": [float("nan"), 40]}), "Invalid"),
])
def test_bad_observation_fails_closed(tmp_path, mutate, error):
    entries = sample()
    mutate(entries[0])
    with pytest.raises(ValueError, match=error):
        load(tmp_path, entries)


def test_duplicate_frame_and_missing_hash_rejected(tmp_path):
    entries = sample()
    with pytest.raises(ValueError, match="Duplicate"):
        load(tmp_path, entries + entries)
    with pytest.raises(ValueError, match="SHA-256"):
        load(tmp_path, sample(), sha_override="f" * 64)


def test_overpopulated_side_is_not_accepted_as_twenty_two(tmp_path):
    entries = sample([observation() for _ in range(12)])
    with pytest.raises(ValueError, match="exceeds eleven"):
        load(tmp_path, entries)


def test_origin_and_match_filename_must_agree(tmp_path):
    source = fixture()
    synthetic_manifest = source.manifest.model_copy(update={
        "origin": FixtureOrigin.MATCHPULSE_SYNTHETIC, "generator_seed": 12,
        "source_url": None,
    })
    synthetic = HistoricalFixture(
        manifest=synthetic_manifest, records=source.records, event_counts={},
        supported_count=0, presentation_count=0, unreviewed_count=0,
    )
    with pytest.raises(ValueError, match="origin"):
        load(tmp_path, sample(), fixture_override=synthetic)
    with pytest.raises(ValueError, match="filename"):
        load_historical_360(
            tmp_path / "wrong-name.json", source, expected_sha256="0" * 64
        )


def test_genuine_off_pitch_source_position_is_preserved_not_clamped(tmp_path):
    frames = sample()
    frames[0]["freeze_frame"][0]["location"] = [120.4, -0.2]
    observation = load(tmp_path, frames).frames[0].observations[0]
    assert observation.position is None
    assert observation.source_location == (120.4, -0.2)
    assert observation.actor


def test_replay_moment_exact_source_event_never_reuses_future_or_prior_frame(tmp_path):
    from matchpulse.providers.statsbomb_360_replay import historical_moment_at_event

    source = fixture()
    frames = load(tmp_path, sample())
    first = historical_moment_at_event(source, frames, "source-action-1")
    assert first.match_id == "3764440"
    assert first.clock_ms == 1250
    assert first.event_sha256 == source.manifest.event_sha256
    assert first.frame_sha256 == frames.frame_sha256
    assert len(first.observed) == len(first.renderable) == 3
    assert first.observed[0].player_id == 99
    assert first.observed[1].player_id is None
    assert not first.full_xi

    # Same source match; different event: must not inherit the prior 360 frame.
    second = historical_moment_at_event(source, frames, "source-action-2")
    assert second.clock_ms == 2000
    assert second.frame is None
    assert second.observed == ()
    assert second.renderable == ()
    assert historical_moment_at_event(source, frames, "source-action-1") == first


def test_replay_moment_keeps_off_field_source_evidence_without_drawing_it(tmp_path):
    from matchpulse.providers.statsbomb_360_replay import historical_moment_at_event

    frame = sample()
    frame[0]["freeze_frame"][1]["location"] = [-2, 82]
    moment = historical_moment_at_event(fixture(), load(tmp_path, frame), "source-action-1")
    assert len(moment.observed) == 3
    assert len(moment.renderable) == 2
    assert moment.observed[1].source_location == (-2, 82)
    assert moment.observed[1].position is None


def test_replay_rejects_wrong_match_fingerprint_or_event_id(tmp_path):
    from matchpulse.providers.statsbomb_360_replay import historical_moment_at_event

    source = fixture()
    frames = load(tmp_path, sample())
    mismatched = source.manifest.model_copy(update={"match_id": "another"})
    wrong_match = HistoricalFixture(
        manifest=mismatched, records=source.records, event_counts={},
        supported_count=0, presentation_count=0, unreviewed_count=0,
    )
    with pytest.raises(ValueError, match="match identity"):
        historical_moment_at_event(wrong_match, frames, "source-action-1")

    fingerprint = source.manifest.model_copy(update={"event_sha256": "c" * 64})
    wrong_hash = HistoricalFixture(
        manifest=fingerprint, records=source.records, event_counts={},
        supported_count=0, presentation_count=0, unreviewed_count=0,
    )
    with pytest.raises(ValueError, match="fingerprint"):
        historical_moment_at_event(wrong_hash, frames, "source-action-1")
    with pytest.raises(ValueError, match="event UUID absent"):
        historical_moment_at_event(source, frames, "unknown")
