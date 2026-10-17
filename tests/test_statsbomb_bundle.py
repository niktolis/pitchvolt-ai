"""Source ID reconciliation must not fabricate absent lineup information."""
import pytest

from matchpulse.fixture_manifest import FixtureManifest, FixtureOrigin
from matchpulse.providers.statsbomb_bundle import validate_historical_bundle
from matchpulse.providers.statsbomb_historical import HistoricalFixture
from matchpulse.providers.statsbomb_lineups import (
    HistoricalLineups,
    HistoricalPlayer,
    HistoricalTeam,
)


def sample():
    manifest = FixtureManifest(
        fixture_id="reference-test", origin=FixtureOrigin.STATSBOMB_OPEN_DATA,
        match_id="9880", event_sha256="b" * 64, event_count=3,
        match_duration_ms=5400000, event_coverage="excerpt",
        source_url="https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/data/events/9880.json",
        attribution="StatsBomb Open Data",
    )
    events = [
        {"type": {"name": "Starting XI"}, "team": {"id": 1}, "player": None},
        {"type": {"name": "Pass"}, "team": {"id": 2}, "player": {"id": 20}},
        {"type": {"name": "Substitution"}, "team": {"id": 1},
         "player": {"id": 10},
         "substitution": {"replacement": {"id": 11}}},
    ]
    fixture = HistoricalFixture(
        manifest=manifest, records=tuple(events), event_counts={},
        supported_count=0, presentation_count=0, unreviewed_count=0,
    )
    roster = HistoricalLineups(
        teams=(
            HistoricalTeam(1, "Fiction A", (
                HistoricalPlayer(10, "One", None, 10, ()),
                HistoricalPlayer(11, "Two", None, 11, ()),
            )),
            HistoricalTeam(2, "Fiction B", (
                HistoricalPlayer(20, "Three", None, 20, ()),
            )),
        ), sha256="c" * 64,
    )
    return fixture, roster


def test_consistent_bundle_and_explicit_substitute():
    fixture, roster = sample()
    report = validate_historical_bundle(fixture, roster)
    assert report.teams_consistent
    assert report.roster_coverage_complete
    assert report.unknown_player_ids == ()
    assert report.source_substitution_count == 1
    assert report.missing_player_references == 1
    assert report.referenced_player_count == 3


def test_unknown_player_is_reported_without_name_fabrication():
    fixture, roster = sample()
    fixture.records[1]["player"]["id"] = 99
    report = validate_historical_bundle(fixture, roster)
    assert report.unknown_player_ids == (99,)
    assert not report.roster_coverage_complete


def test_opposing_team_player_rejected():
    fixture, roster = sample()
    fixture.records[1]["player"]["id"] = 10
    with pytest.raises(ValueError, match="opposing team"):
        validate_historical_bundle(fixture, roster)


def test_substitute_must_belong_to_event_team():
    fixture, roster = sample()
    fixture.records[2]["substitution"]["replacement"]["id"] = 20
    with pytest.raises(ValueError, match="opposing team"):
        validate_historical_bundle(fixture, roster)


def test_unknown_event_team_rejected():
    fixture, roster = sample()
    fixture.records[0]["team"]["id"] = 3
    with pytest.raises(ValueError, match="unknown team"):
        validate_historical_bundle(fixture, roster)


def test_substitution_requires_source_replacement():
    fixture, roster = sample()
    fixture.records[2]["substitution"] = {}
    with pytest.raises(ValueError, match="replacement identity"):
        validate_historical_bundle(fixture, roster)
