"""Keep historical player and team identities source-backed."""
import hashlib
import json

import pytest

from matchpulse.providers.statsbomb_lineups import load_historical_lineups


def setup(tmp_path, teams):
    data = json.dumps(teams).encode()
    path = tmp_path / "lineups.json"
    path.write_bytes(data)
    return path, hashlib.sha256(data).hexdigest()


def teams():
    return [
        {
            "team_id": 1,
            "team_name": "Source Home",
            "lineup": [{
                "player_id": 11,
                "player_name": "Source Player",
                "player_nickname": None,
                "jersey_number": 9,
                "positions": [{"position": "Center Forward"}],
            }],
        },
        {"team_id": 2, "team_name": "Source Away", "lineup": []},
    ]


def test_history_roster_is_source_backed_and_hash_pinned(tmp_path):
    path, sha = setup(tmp_path, teams())
    projected = load_historical_lineups(path, expected_sha256=sha)
    assert projected.sha256 == sha
    assert projected.teams[0].name == "Source Home"
    assert projected.teams[0].players[0].name == "Source Player"
    assert projected.teams[0].players[0].jersey_number == 9
    assert projected.teams[0].players[0].positions == ("Center Forward",)
    assert projected.teams[1].players == ()


def test_lineup_tamper_rejected(tmp_path):
    path, sha = setup(tmp_path, teams())
    path.write_text("[]")
    with pytest.raises(ValueError, match="SHA-256"):
        load_historical_lineups(path, expected_sha256=sha)


def test_player_team_duplicates_rejected(tmp_path):
    roster = teams()
    roster[0]["lineup"].append(dict(roster[0]["lineup"][0]))
    path, sha = setup(tmp_path, roster)
    with pytest.raises(ValueError, match="Duplicate player"):
        load_historical_lineups(path, expected_sha256=sha)
    roster = teams()
    roster[1]["team_id"] = 1
    path, sha = setup(tmp_path, roster)
    with pytest.raises(ValueError, match="Duplicate team"):
        load_historical_lineups(path, expected_sha256=sha)
