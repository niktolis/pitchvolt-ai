"""Unified offline verified historical fixture integration, no network dependency."""
import hashlib
import json

import pytest

from pitchvolt.fixture_manifest import FixtureManifest, FixtureOrigin
from pitchvolt.statsbomb_bundle_report import load_verified_historical_bundle


def sample(tmp_path):
    events = [
        {"id": "a", "index": 1, "period": 1, "timestamp": "00:00:01.000",
         "minute": 0, "second": 1, "type": {"name": "Pass"},
         "team": {"id": 1, "name": "Home"}, "player": {"id": 10, "name": "Home 10"},
         "location": [60, 40], "pass": {"end_location": [70, 40]}},
        {"id": "b", "index": 2, "period": 1, "timestamp": "00:00:02.000",
         "minute": 0, "second": 2, "type": {"name": "Shot"},
         "team": {"id": 2, "name": "Away"}, "player": {"id": 20, "name": "Away 20"},
         "location": [100, 40], "shot": {"outcome": {"name": "Goal"}}},
    ]

    def players(ident: int) -> dict[str, object]:
        return {
            "player_id": ident, "player_name": f"Player {ident}",
            "player_nickname": None, "jersey_number": ident,
            "positions": [],
        }
    lineups = [
        {"team_id": 1, "team_name": "Home", "lineup": [players(10)]},
        {"team_id": 2, "team_name": "Away", "lineup": [players(20)]},
    ]
    raw_events = json.dumps(events).encode()
    raw_lineups = json.dumps(lineups).encode()
    (tmp_path / "9880.json").write_bytes(raw_events)
    (tmp_path / "9880.lineups.json").write_bytes(raw_lineups)
    manifest = FixtureManifest(
        fixture_id="statsbomb-9880-test", match_id="9880",
        origin=FixtureOrigin.STATSBOMB_OPEN_DATA,
        event_sha256=hashlib.sha256(raw_events).hexdigest(),
        event_count=2, match_duration_ms=2000, event_coverage="excerpt",
        source_url="https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/data/events/9880.json",
        attribution="StatsBomb Open Data",
    )
    (tmp_path / "9880.manifest.json").write_text(manifest.model_dump_json())
    return hashlib.sha256(raw_lineups).hexdigest()


def test_bundle_coordinates_identity_and_non_authoritative_excerpt_score(tmp_path):
    sha = sample(tmp_path)
    result = load_verified_historical_bundle(tmp_path, match_id="9880", lineup_sha256=sha)
    assert result.identity.roster_coverage_complete
    assert result.identity.teams_consistent
    assert result.projection.source_event_count == 2
    assert len(result.projection.actions) == 2
    assert result.projection.actions[0].location_x == 52.5
    assert result.state.goals[0].event_id == "b"
    assert result.state.score_by_team is None
    assert result.state.score_unavailable_reason == "excerpt_without_authoritative_initial_score"


def test_bundle_rejects_tampered_lineup(tmp_path):
    sha = sample(tmp_path)
    (tmp_path / "9880.lineups.json").write_text("[]")
    with pytest.raises(ValueError, match="SHA-256"):
        load_verified_historical_bundle(tmp_path, match_id="9880", lineup_sha256=sha)


def test_bundle_rejects_invalid_match_selector(tmp_path):
    with pytest.raises(ValueError, match="numeric"):
        load_verified_historical_bundle(tmp_path, match_id="../etc", lineup_sha256="a" * 64)
