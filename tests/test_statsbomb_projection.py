"""Historical projection preserves source evidence and does not infer tactics."""
from matchpulse.fixture_manifest import FixtureManifest, FixtureOrigin
from matchpulse.providers.statsbomb_historical import HistoricalFixture
from matchpulse.providers.statsbomb_projection import project_historical_actions


def fixture(records):
    return HistoricalFixture(
        manifest=FixtureManifest(
            fixture_id="fixture-1", match_id="1", origin=FixtureOrigin.STATSBOMB_OPEN_DATA,
            event_sha256="a" * 64, event_count=len(records),
            match_duration_ms=5400000, event_coverage="excerpt",
            source_url="https://github.com/hudl/open-data/blob/master/data/events/1.json",
            attribution="StatsBomb Open Data",
        ),
        records=tuple(records), event_counts={}, supported_count=0,
        presentation_count=0, unreviewed_count=0,
    )


def event(kind, index, second, **fields):
    return {
        "id": f"source-{index}", "index": index, "period": 1,
        "minute": 0, "second": second,
        "timestamp": f"00:00:{second:02d}.250",
        "type": {"name": kind}, "team": {"name": "Home"},
        "player": {"name": "Player"}, "location": [60, 40], **fields,
    }


def test_project_pass_retains_source_id_and_normalized_coordinates():
    raw = [event("Pass", 1, 1, **{"pass": {"end_location": [120, 80]}})]
    result = project_historical_actions(fixture(raw))
    assert result.complete
    assert result.actions[0].event_id == "source-1"
    assert result.actions[0].clock_ms == 1250
    assert (result.actions[0].location_x, result.actions[0].location_y) == (52.5, 34)
    assert (result.actions[0].destination_x, result.actions[0].destination_y) == (105, 68)


def test_unsupported_actions_are_reported_without_inventing_turnovers():
    result = project_historical_actions(fixture([
        event("Ball Recovery", 1, 1),
        event("Substitution", 2, 2),
        event("Pressure", 3, 3),
    ]))
    assert len(result.actions) == 1
    assert result.actions[0].kind == "pressure"
    assert result.omitted_by_type == {"Ball Recovery": 1, "Substitution": 1}
    assert not result.complete


def test_missing_player_and_destination_omitted():
    missing = event("Pass", 1, 1)
    missing["player"] = None
    result = project_historical_actions(fixture([missing, event("Shot", 2, 2)]))
    assert result.actions == ()
    assert result.omitted_by_type == {"Pass": 1, "Shot": 1}
