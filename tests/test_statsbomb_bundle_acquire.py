"""Two-file acquisition preserves original bytes and fails closed."""
import json

import pytest

from pitchvolt.statsbomb_bundle_acquire import (
    pinned_bundle_urls,
    pinned_three_sixty_urls,
    prepare_historical_bundle,
)

COMMIT = "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"


def source():
    events = [
        {"id": "source-one", "index": 1, "period": 1,
         "timestamp": "00:00:01.000", "minute": 0, "second": 1,
         "type": {"name": "Pressure"}, "team": {"id": 1, "name": "Home"},
         "player": {"id": 11, "name": "Player 11"}, "location": [60, 40]},
        {"id": "source-two", "index": 2, "period": 1,
         "timestamp": "00:00:02.000", "minute": 0, "second": 2,
         "type": {"name": "Pressure"}, "team": {"id": 2, "name": "Away"},
         "player": {"id": 22, "name": "Player 22"}, "location": [80, 40]},
    ]
    roster = [
        {"team_id": 1, "team_name": "Home",
         "lineup": [{"player_id": 11, "player_name": "Player 11"}]},
        {"team_id": 2, "team_name": "Away",
         "lineup": [{"player_id": 22, "player_name": "Player 22"}]},
    ]
    return json.dumps(events).encode(), json.dumps(roster).encode()


def test_both_url_paths_share_immutable_commit():
    event, lineup = pinned_bundle_urls(COMMIT, "9880")
    assert f"/{COMMIT}/data/events/9880.json" in event
    assert f"/{COMMIT}/data/lineups/9880.json" in lineup


def test_verified_bundle_acquisition_without_external_calls(tmp_path):
    event, lineup = source()
    result = prepare_historical_bundle(
        event, lineup, commit=COMMIT, match_id="9880", directory=tmp_path
    )
    assert result["event_count"] == 2
    assert result["projected_count"] == 2
    assert (tmp_path / "9880.json").read_bytes() == event
    assert (tmp_path / "9880.lineups.json").read_bytes() == lineup
    with pytest.raises(FileExistsError):
        prepare_historical_bundle(
            event, lineup, commit=COMMIT, match_id="9880", directory=tmp_path
        )


def test_bad_roster_rolls_back_both_files(tmp_path):
    event, _ = source()
    with pytest.raises(ValueError, match="two historical"):
        prepare_historical_bundle(
            event, b"[]", commit=COMMIT, match_id="9880", directory=tmp_path
        )
    assert list(tmp_path.iterdir()) == []


def test_unknown_roster_player_reports_gap_without_fabrication(tmp_path):
    event, lineup = source()
    roster = json.loads(lineup)
    roster[0]["lineup"][0]["player_id"] = 99
    result = prepare_historical_bundle(
        event, json.dumps(roster).encode(),
        commit=COMMIT, match_id="9880", directory=tmp_path
    )
    assert result["event_count"] == 2


def three_sixty():
    return json.dumps([{
        "event_uuid": "source-one",
        "visible_area": [0, 0, 120, 0, 120, 80, 0, 80],
        "freeze_frame": [
            {"teammate": True, "actor": True, "keeper": False,
             "location": [60, 40]},
            {"teammate": False, "actor": False, "keeper": True,
             "location": [10, 40]},
        ],
    }]).encode()


def test_triple_urls_are_same_commit_and_match():
    urls = pinned_three_sixty_urls(COMMIT, "3764440")
    assert len(urls) == 3
    for url in urls:
        assert f"/{COMMIT}/" in url
        assert "/3764440.json" in url
    assert "/data/three-sixty/" in urls[2]


def test_optional_three_file_acquisition_and_fingerprint(tmp_path):
    import hashlib

    events, lineups = source()
    frames = three_sixty()
    result = prepare_historical_bundle(
        events, lineups, three_sixty=frames,
        commit=COMMIT, match_id="3764440", directory=tmp_path,
    )
    assert result["frame_count"] == 1
    assert result["full_xi_frame_count"] == 0
    assert result["frame_sha256"] == hashlib.sha256(frames).hexdigest()
    assert (tmp_path / "3764440.360.json").read_bytes() == frames
    assert (tmp_path / "3764440.lineups.json").read_bytes() == lineups


def test_invalid_three_sixty_rolls_back_entire_original_bundle(tmp_path):
    events, lineups = source()
    incompatible = json.loads(three_sixty())
    incompatible[0]["event_uuid"] = "event-from-wrong-match"
    with pytest.raises(ValueError, match="absent from source events"):
        prepare_historical_bundle(
            events, lineups, three_sixty=json.dumps(incompatible).encode(),
            commit=COMMIT, match_id="3764440", directory=tmp_path,
        )
    assert list(tmp_path.iterdir()) == []


def test_missing_three_sixty_does_not_change_existing_two_file_contract(tmp_path):
    events, lineups = source()
    result = prepare_historical_bundle(
        events, lineups, commit=COMMIT, match_id="3764440", directory=tmp_path,
    )
    assert "frame_sha256" not in result
    assert not (tmp_path / "3764440.360.json").exists()
