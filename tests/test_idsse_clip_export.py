"""Deterministic source clip contract checks using original authored *test* samples."""
import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest

from pitchvolt.idsse_clip_export import (
    EVENT_FRAME,
    EVENT_ID,
    FIRST_FRAME,
    SAMPLE_COUNT,
    _make_clip,
    export_verified_clip,
    verify_compact_asset,
)

HOME = "DFL-CLU-HOME"
AWAY = "DFL-CLU-AWAY"
SHOT_TIME = datetime(2023, 5, 27, 13, 31, 53, 360000, tzinfo=UTC)


def toy_source():
    roster = {
        **{f"home-{i:02d}": HOME for i in range(11)},
        **{f"away-{i:02d}": AWAY for i in range(11)},
    }
    teams = [
        {"id": HOME, "name": "Home (TEST)", "role": "home"},
        {"id": AWAY, "name": "Away (TEST)", "role": "away"},
    ]
    start = SHOT_TIME - timedelta(seconds=(EVENT_FRAME - FIRST_FRAME) / 25)
    rows = {}
    for n in range(SAMPLE_COUNT):
        players = {
            player: (
                i * 0.5 - 6 + n * 0.002,
                (i % 11) * 0.4 - 3,
            )
            for i, player in enumerate(sorted(roster))
        }
        rows[FIRST_FRAME + n] = {
            "time": start + timedelta(milliseconds=40 * n),
            "players": players,
            "ball": ((-1 + n * 0.01, 2.25, 0.12 + n * 0.001), "1"),
            "ball_possession": "2",
        }
    shot = {
        "source_event_id": EVENT_ID,
        "calculated_frame": EVENT_FRAME,
        "source_timestamp": SHOT_TIME.isoformat(),
    }
    return rows, roster, teams, shot


def payload():
    rows, roster, teams, shot = toy_source()
    return _make_clip(
        rows, roster=roster, teams=teams, shot=shot,
        metadata_sha="a" * 64, events_sha="b" * 64,
    )


def _write(tmp_path, data):
    path = tmp_path / "source-observed-test.json"
    path.write_bytes(
        (json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
         + "\n").encode("utf-8")
    )
    return path


def test_observed_25_second_clip_roundtrip_at_source_exact_sample_times(tmp_path):
    data = payload()
    path = _write(tmp_path, data)
    summary = verify_compact_asset(
        path, expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest()
    )
    assert summary["frame_count"] == 625
    assert summary["players_per_frame"] == 22
    assert summary["ball_xyz_frames"] == 625
    assert summary["exact_shot_aligned"]
    assert not summary["public_replay_enabled"]
    assert data["segment"]["first_frame"] == FIRST_FRAME
    assert data["segment"]["last_frame"] == FIRST_FRAME + SAMPLE_COUNT - 1
    assert data["segment"]["duration_seconds"] == 25
    assert data["source"]["license"] == "CC-BY-4.0"
    assert "Deutsche Fußball Liga" in data["source"]["attribution"]
    assert not data["player_carrier_known"]
    assert data["coordinates"]["no_interpolation"] is True


def test_source_coordinate_translation_does_not_clamp_or_infer_motion():
    original, roster, teams, shot = toy_source()
    original[FIRST_FRAME]["ball"] = ((-53.1, 0.0, 0.27), "0")
    data = _make_clip(
        original, roster=roster, teams=teams, shot=shot,
        metadata_sha="a" * 64, events_sha="b" * 64,
    )
    assert data["frames"][0]["ball_xyz_m"] == [-0.6000000000000014, 34.0, 0.27]
    assert data["frames"][0]["source_ball_status"] == "0"
    assert len(data["frames"]) == 625
    assert all(len(f["players_xy_m"]) == 22 for f in data["frames"])
    assert len({row["timestamp"] for row in data["frames"]}) == SAMPLE_COUNT


@pytest.mark.parametrize("mutate", [
    lambda d: d["frames"][4].update({"source_frame": -1}),
    lambda d: d["frames"][7].update({"ball_xyz_m": None}),
    lambda d: d["frames"][12].update({"players_xy_m": [None] * 22}),
    lambda d: d["frames"][22].update({"timestamp": d["frames"][21]["timestamp"]}),
    lambda d: d.update({"public_replay_enabled": True}),
    lambda d: d["segment"].update({"source_shot_frame": 111}),
])
def test_compact_decoder_rejects_missing_or_invented_source(tmp_path, mutate):
    data = payload()
    mutate(data)
    with pytest.raises(ValueError):
        verify_compact_asset(_write(tmp_path, data))


def test_source_encoder_rejects_missing_player_ball_frame_and_shot_mismatch():
    for modify, msg in [
        (lambda rows: rows.pop(FIRST_FRAME + 19), "missing or out-of-order"),
        (lambda rows: rows[FIRST_FRAME]["players"].pop("home-00"), "exactly 22"),
        (lambda rows: rows[FIRST_FRAME].update({"ball": (None, "1")}), "ball XYZ"),
        (
            lambda rows: rows[FIRST_FRAME + 100].update({
                "time": rows[FIRST_FRAME + 100]["time"] + timedelta(milliseconds=15),
            }),
            "continuous at 25 Hz",
        ),
    ]:
        rows, roster, teams, shot = toy_source()
        modify(rows)
        with pytest.raises(ValueError, match=msg):
            _make_clip(
                rows, roster=roster, teams=teams, shot=shot,
                metadata_sha="a" * 64, events_sha="b" * 64,
            )


def test_export_is_fail_closed_for_wrong_match_and_output_collision(tmp_path):
    source = tmp_path / "wrong-game"
    source.mkdir()
    with pytest.raises(ValueError, match="immutable source match"):
        export_verified_clip(
            source, metadata_sha256="a" * 64, events_sha256="b" * 64,
            destination=tmp_path / "derived.json",
        )
    correct = tmp_path / "J03WMX"
    correct.mkdir()
    outfile = tmp_path / "derived.json"
    outfile.write_text("existing user bytes")
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        export_verified_clip(
            correct, metadata_sha256="a" * 64, events_sha256="b" * 64,
            destination=outfile,
        )
    assert outfile.read_text() == "existing user bytes"


def test_canonical_json_encoder_is_deterministic_for_same_observed_bytes(tmp_path):
    data1 = _write(tmp_path, payload()).read_bytes()
    data2 = _write(tmp_path, payload()).read_bytes()
    assert data1 == data2
    assert hashlib.sha256(data1).hexdigest() == hashlib.sha256(data2).hexdigest()
