"""Golden replay dataset contracts across fictional and independently sourced records."""
from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from pitchvolt.api import app, timeline
from pitchvolt.events import EventType, Point
from pitchvolt.fixture_manifest import FixtureManifest, FixtureOrigin
from pitchvolt.providers.statsbomb_historical import HistoricalFixture
from pitchvolt.replay_dataset import (
    HistoricalReplaySource,
    ReplayDataset,
    SyntheticReplaySource,
)
from pitchvolt.scenarios import SCENARIO_NAMES, scenario


@pytest.mark.parametrize("name", SCENARIO_NAMES)
def test_synthetic_dataset_matches_existing_unmodified_api(name: str) -> None:
    dataset = SyntheticReplaySource(name).load()
    match, events = scenario(name)
    assert dataset.origin == FixtureOrigin.PITCHVOLT_SYNTHETIC
    assert dataset.permits_tactical_processing
    assert dataset.canonical_match == match
    assert dataset.canonical_events == tuple(events)
    assert dataset.manifest.match_id == match.match_id
    assert dataset.manifest.event_count == dataset.projected_count == len(events)
    assert dataset.manifest.generator_seed == 42
    assert dataset.manifest.source_url is None
    assert all(action.player_id is not None for action in dataset.actions)

    published = timeline(name)
    assert [a.event_id for a in dataset.actions] == [
        m.payload.event_id for m in published if m.kind == "match_event"
    ]
    client = TestClient(app)
    assert len(client.get(f"/api/matches/{name}/timeline").json()) == len(published)


def test_replay_dataset_fingerprint_and_coverage_are_reproducible() -> None:
    initial = SyntheticReplaySource("extended_match", seed=42).load()
    replayed = SyntheticReplaySource("extended_match", seed=42).load()
    changed = SyntheticReplaySource("extended_match", seed=43).load()
    assert initial.manifest.event_sha256 == replayed.manifest.event_sha256
    assert initial.manifest.event_sha256 != changed.manifest.event_sha256
    assert initial.manifest.event_coverage == "full_match"
    assert initial.actions[0].clock_ms == 0
    assert initial.actions[-1].clock_ms == 5_400_000
    assert SyntheticReplaySource("high_press").load().manifest.event_coverage == "excerpt"
    assert SyntheticReplaySource("sustained_possession").load().manifest.event_coverage == "excerpt"


def test_cursor_exactness_rewind_tied_clocks_and_negative_checks() -> None:
    data = SyntheticReplaySource("extended_match").load()
    a0, a1 = data.actions[:2]
    assert data.at_cursor(0).latest_event == a0
    assert data.at_cursor(a1.clock_ms).latest_event == a1
    assert data.at_cursor(a1.clock_ms - 1).latest_event == a0
    stale = data.at_cursor(a1.clock_ms + 1)
    assert stale.latest_event == a1
    assert not stale.observation_at_cursor
    assert data.at_cursor(a0.clock_ms).observation_at_cursor
    assert data.at_cursor(5_400_000).visible_action_count == 220
    assert data.at_cursor(0).visible_action_count == 1
    with pytest.raises(ValueError, match="nonnegative"):
        data.at_cursor(-1)
    with pytest.raises(ValueError, match="nonnegative"):
        data.at_cursor(1.3)  # type: ignore[arg-type]

    # Modifying the clock of a canonical synthetic source action is rejected.
    with pytest.raises(ValueError, match="diverged"):
        replace(data, actions=(a0, replace(a1, clock_ms=a0.clock_ms), *data.actions[2:]))


def test_legacy_excerpt_does_not_invent_kickoff_or_score() -> None:
    data = SyntheticReplaySource("high_press").load()
    earliest = data.actions[0].clock_ms
    assert earliest > 0
    assert data.at_cursor(earliest - 1).latest_event is None
    assert data.manifest.event_coverage == "excerpt"
    assert data.canonical_events[0].event_type == EventType.PRESSURE
    assert not hasattr(data, "score_by_team")


def historical_source_fixture() -> HistoricalFixture:
    raw = (
        {
            "id": "start-1", "index": 1, "period": 1, "minute": 0, "second": 0,
            "timestamp": "00:00:00.000", "type": {"name": "Starting XI"},
            "team": {"id": 1, "name": "Recorded home"},
        },
        {
            "id": "pass-1", "index": 2, "period": 1, "minute": 0, "second": 1,
            "timestamp": "00:00:01.250", "type": {"name": "Pass"},
            "team": {"id": 1, "name": "Recorded home"},
            "player": {"id": 20, "name": "Source Player"},
            "location": [60, 40], "pass": {"end_location": [120, 80]},
        },
        {
            "id": "off-1", "index": 3, "period": 1, "minute": 0, "second": 2,
            "timestamp": "00:00:02.000", "type": {"name": "Foul Committed"},
            "team": {"id": 2, "name": "Recorded away"},
        },
        {
            "id": "shot-1", "index": 4, "period": 1, "minute": 0, "second": 3,
            "timestamp": "00:00:03.500", "type": {"name": "Shot"},
            "team": {"id": 1, "name": "Recorded home"},
            "player": {"id": 20, "name": "Source Player"},
            "location": [100, 40], "shot": {"outcome": {"name": "Goal"}},
        },
    )
    manifest = FixtureManifest(
        fixture_id="historical-test", origin=FixtureOrigin.STATSBOMB_OPEN_DATA,
        match_id="123", event_sha256="f" * 64, event_count=len(raw),
        event_coverage="excerpt", match_duration_ms=5_400_000,
        source_url="https://github.com/hudl/open-data/blob/pinned/data/events/123.json",
        attribution="StatsBomb Open Data",
    )
    # Offline unit fixture: real acquisition uses the independently verified
    # load_historical_fixture, which enforces the event SHA before this adapter.
    return HistoricalFixture(
        manifest=manifest, records=raw, event_counts={},
        supported_count=2, presentation_count=1, unreviewed_count=1,
    )


def test_historical_dataset_keeps_names_and_omission_counts_without_claiming_ids() -> None:
    source = historical_source_fixture()
    data = HistoricalReplaySource(source).load()
    assert data.origin == FixtureOrigin.STATSBOMB_OPEN_DATA
    assert not data.permits_tactical_processing
    assert data.canonical_match is None and data.canonical_events == ()
    assert data.manifest.event_count == 4 and data.projected_count == 2
    assert data.omitted_by_type == (("Foul Committed", 1), ("Starting XI", 1))
    first, second = data.actions
    assert first.event_id == "pass-1" and first.source_index == 2
    assert first.team_id is None and first.player_id is None
    assert first.team_label == "Recorded home"
    assert first.player_label == "Source Player"
    assert first.location == Point(x=52.5, y=34)
    assert first.destination == Point(x=105, y=68)
    assert second.kind == "shot"
    assert second.destination is None  # missing shot endpoint is NOT fabricated
    assert data.at_cursor(1_249).latest_event is None
    assert data.at_cursor(1_250).observation_at_cursor
    assert data.at_cursor(2_500).latest_event == first
    assert not data.at_cursor(2_500).observation_at_cursor
    # Same-clock source observations resolve by original source event index.
    tied = replace(data, actions=(first, replace(second, clock_ms=first.clock_ms)))
    assert tied.at_cursor(first.clock_ms).latest_event.event_id == "shot-1"


def test_replay_dataset_refuses_fiction_history_mixing_and_reordered_inputs() -> None:
    source = HistoricalReplaySource(historical_source_fixture()).load()
    synthetic = SyntheticReplaySource("high_press").load()
    with pytest.raises(ValueError, match="only for synthetic"):
        replace(source, canonical_match=synthetic.canonical_match)
    with pytest.raises(ValueError, match="Historical"):
        replace(source, canonical_events=synthetic.canonical_events)
    with pytest.raises(ValueError, match="not verified canonical"):
        replace(source, actions=(replace(source.actions[0], player_id="20"),))
    with pytest.raises(ValueError, match="ordered"):
        replace(source, actions=tuple(reversed(source.actions)))
    with pytest.raises(ValueError, match="Duplicate"):
        replace(synthetic, actions=(synthetic.actions[0], synthetic.actions[0]))
    with pytest.raises(ValueError, match="canonical"):
        replace(synthetic, canonical_events=())
    with pytest.raises(ValueError, match="origin"):
        HistoricalReplaySource(
            replace(historical_source_fixture(), manifest=synthetic.manifest)
        ).load()


def test_source_coverage_does_not_implicitly_authorize_historical_api_or_ai() -> None:
    source = historical_source_fixture()
    from pitchvolt.api import _load

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        _load(source.manifest.match_id)
    assert exc.value.status_code == 404
    assert TestClient(app).get("/api/matches/123/timeline").status_code == 404
    assert SyntheticReplaySource("high_press").load().manifest.origin != source.manifest.origin
