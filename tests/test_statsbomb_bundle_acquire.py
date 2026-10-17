"""Two-file acquisition preserves original bytes and fails closed."""
import json

import pytest

from matchpulse.statsbomb_bundle_acquire import (
    pinned_bundle_urls,
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
