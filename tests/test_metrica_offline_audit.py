"""Only original *synthetic test fixtures* are used. No Metrica bytes in this repo."""

import csv
import hashlib

import pytest

from pitchvolt.metrica_offline_audit import inspect_game, upstream_path

COMMIT = "e706dd506b360d69d9d123d5b8026e7294b13996"


def _csv_file(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sample(tmp_path, *, game=1, mismatch=False, home_missing_ball=False):
    directory = tmp_path / f"Sample_Game_{game}"
    directory.mkdir()
    expected = {}
    for team in ("Home", "Away"):
        name = f"Sample_Game_{game}_RawTrackingData_{team}_Team.csv"
        rows = [
            ["", "", "", team, "", "", "", "", ""],
            ["", "", "", "11", "", "12", "", "Ball", ""],
            ["Period", "Frame", "Time [s]", "P1", "", "P2", "", "Ball", ""],
        ]
        for frame in (1, 2, 3):
            stamp = frame / 25 + (0.04 if mismatch and team == "Away" and frame == 2 else 0)
            ball = ["", ""] if home_missing_ball and team == "Home" else ["0.5", "0.5"]
            rows.append([1, frame, stamp, "0.2", "0.3", "", "", *ball])
        expected[team] = _csv_file(directory / name, rows)
    expected["Events"] = _csv_file(
        directory / f"Sample_Game_{game}_RawEventsData.csv",
        [
            [
                "Team", "Type", "Subtype", "Period", "Start Frame", "Start Time [s]",
                "End Frame", "End Time [s]", "From", "To",
                "Start X", "Start Y", "End X", "End Y",
            ],
            ["Home", "PASS", "", 1, 1, 0.04, 2, 0.08, "Player11", "Player12",
             0.2, 0.3, 0.3, 0.5],
            ["Away", "RECOVERY", "", 1, 3, 0.12, 3, 0.12, "Player16", "", "", "", "", ""],
        ],
    )
    return directory, expected


def _synthetic_manifest(path, game):
    """Expected object identities generated from original synthetic tests, not upstream."""
    manifest = {}
    for kind in ("Home", "Away", "Events"):
        stem = f"Sample_Game_{game}_Raw"
        name = stem + ("EventsData.csv" if kind == "Events" else
                       f"TrackingData_{kind}_Team.csv")
        data = (path / name).read_bytes()
        git_blob = hashlib.sha1(f"blob {len(data)}\\0".encode() + data).hexdigest()
        manifest[kind] = (git_blob, len(data))
    return manifest


def _run(path, hashes, **overrides):
    game = overrides.pop("game", 1)
    manifest = overrides.pop("test_manifest", None)
    if manifest is None:
        manifest = _synthetic_manifest(path, int(path.name.removeprefix("Sample_Game_")))
    return inspect_game(
        path, game=game, commit=overrides.pop("commit", COMMIT),
        expected_sha256=hashes, max_frames=overrides.pop("max_frames", 3),
        _test_git_blob_manifest=manifest, **overrides,
    )


def test_offline_pinned_sample_reports_only_aggregates_and_explicit_rights_block(tmp_path):
    directory, hashes = _sample(tmp_path)
    report = _run(directory, hashes)
    assert report["source_commit"] == COMMIT
    assert report["canonical_upstream_blob_identity_verified"] is False
    assert report["game"] == 1
    assert report["frame_rate_hz"] == 25
    assert report["tracking_frames_synchronized"] is True
    assert report["events_joined_to_sample"] is True
    assert report["events"]["events_examined"] == 2
    assert report["events"]["events_with_examined_tracking_frame"] == 2
    assert report["teams"]["Home"]["player_slots"] == 2
    assert report["teams"]["Away"]["visible_players_max"] == 1
    assert report["teams"]["Home"]["ball_samples"]["observed"] == 3
    assert report["teams"]["Home"]["player_samples"]["missing"] == 3
    assert report["license_status"] == "UNVERIFIED_DO_NOT_REDISTRIBUTE"
    assert report["may_publish_source_data"] is False
    assert report["may_serve_tracking_replay"] is False
    assert "coordinates" not in str(report)
    assert report["source_files"]["Events"]["sha256"] == hashes["Events"]
    assert report["source_files"]["Home"]["url"].startswith(
        f"https://github.com/metrica-sports/sample-data/blob/{COMMIT}/data/"
    )


def test_missing_ball_remains_unknown_and_does_not_affect_player_coverage(tmp_path):
    directory, hashes = _sample(tmp_path, home_missing_ball=True)
    report = _run(directory, hashes)
    assert report["teams"]["Home"]["ball_samples"]["missing"] == 3
    assert report["teams"]["Home"]["ball_samples"]["observed"] == 0
    assert report["teams"]["Away"]["ball_samples"]["observed"] == 3


def test_game_identity_is_enforced_without_cross_fixture_joins(tmp_path):
    directory, hashes = _sample(tmp_path, game=2)
    with pytest.raises(ValueError, match="same Metrica sample game"):
        _run(directory, hashes, game=1)
    assert _run(directory, hashes, game=2)["game"] == 2


def test_source_pins_never_accept_branches_unsafe_paths_or_uppercase_hashes():
    assert "/blob/" + COMMIT + "/" in upstream_path(2, "Home", commit=COMMIT)
    for game, kind, commit in [(3, "Home", COMMIT), (1, "../evil", COMMIT),
                               (1, "Away", "master"), (1, "Home", "F" * 40)]:
        with pytest.raises(ValueError):
            upstream_path(game, kind, commit=commit)


def test_sha256_mismatch_aborts_before_source_parsing(tmp_path):
    directory, hashes = _sample(tmp_path)
    hashes["Home"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _run(directory, hashes)


def test_invalid_pins_and_missing_pins_fail_closed(tmp_path):
    directory, hashes = _sample(tmp_path)
    with pytest.raises(ValueError, match="Exactly Home"):
        _run(directory, {"Home": hashes["Home"]})
    hashes["Events"] = "not-a-digest"
    with pytest.raises(ValueError, match="64 lower-case"):
        _run(directory, hashes)


def test_home_away_sample_timestamps_must_be_synchronized(tmp_path):
    directory, hashes = _sample(tmp_path, mismatch=True)
    with pytest.raises(ValueError, match="not synchronized"):
        _run(directory, hashes)


def test_no_network_only_operator_local_files_are_read(tmp_path, monkeypatch):
    directory, hashes = _sample(tmp_path)
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Unexpected outbound HTTP")
    monkeypatch.setattr("urllib.request.urlopen", forbidden)
    assert _run(directory, hashes)["teams"]["Home"]["frames_examined"] == 3


@pytest.mark.parametrize("limit", [0, 1, 5001])
def test_bounded_read_rejects_invalid_frame_sample_limit(tmp_path, limit):
    directory, hashes = _sample(tmp_path)
    with pytest.raises(ValueError, match="2..5000"):
        _run(directory, hashes, max_frames=limit)


def test_invalid_coordinate_pair_is_not_silently_positioned(tmp_path):
    directory, hashes = _sample(tmp_path)
    home = directory / "Sample_Game_1_RawTrackingData_Home_Team.csv"
    raw = home.read_text()
    home.write_text(raw.replace("0.5,0.5\n", "0.5,\n", 1))
    hashes["Home"] = hashlib.sha256(home.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="Incomplete tracking x/y"):
        _run(directory, hashes)


def test_event_exposure_is_aggregate_and_does_not_include_row_content(tmp_path):
    directory, hashes = _sample(tmp_path)
    report = _run(directory, hashes)
    assert "Player11" not in str(report)
    assert "0.2" not in str(report)


def test_upstream_provenance_rejects_correct_sha256_for_wrong_bytes(tmp_path):
    """SHA-256 pin from an operator does NOT establish the upstream git object."""
    path, hashes = _sample(tmp_path)
    original_manifest = _synthetic_manifest(path, 1)
    home_file = path / "Sample_Game_1_RawTrackingData_Home_Team.csv"
    home_file.write_text(home_file.read_text().replace("0.2", "0.4", 1))
    hashes["Home"] = hashlib.sha256(home_file.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="Git blob mismatch"):
        _run(path, hashes, test_manifest=original_manifest)


def test_original_upstream_manifest_does_not_accept_synthetic_fixture(tmp_path):
    """The production auditor cannot label our synthetic tests as Metrica data."""
    directory, hashes = _sample(tmp_path)
    with pytest.raises(ValueError, match="Upstream pinned file size mismatch"):
        inspect_game(
            directory, game=1, commit=COMMIT,
            expected_sha256=hashes, max_frames=3,
        )


def test_cross_period_frame_is_not_falsely_joined(tmp_path):
    directory, hashes = _sample(tmp_path)
    events = directory / "Sample_Game_1_RawEventsData.csv"
    with events.open(newline="", encoding="utf-8") as src:
        rows = list(csv.reader(src))
    rows[2][3] = "2"  # frame 3 belongs to period 2 now, not sampled period 1
    hashes["Events"] = _csv_file(events, rows)
    report = _run(directory, hashes)
    assert report["events"]["events_examined"] == 2
    assert report["events"]["events_with_examined_tracking_frame"] == 1
    assert report["events_joined_to_sample"] is True


def test_different_upstream_commit_is_not_misrepresented(tmp_path):
    directory, hashes = _sample(tmp_path)
    with pytest.raises(ValueError, match="Only the audited immutable upstream commit"):
        _run(directory, hashes, commit="0" * 40)
