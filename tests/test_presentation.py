"""Authored fictional team profiles, unknown excerpts and source-goal scoring."""
from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from pitchvolt.api import app
from pitchvolt.events import EventType, Outcome
from pitchvolt.fixture_manifest import FixtureOrigin
from pitchvolt.presentation import (
    FictionalPlayer,
    MatchPresentation,
    SubstitutionFact,
    TeamPresentation,
    active_actor_id,
    authored_substitutions,
    build_presentation,
)
from pitchvolt.replay_dataset import SyntheticReplaySource

client = TestClient(app)


@pytest.mark.parametrize("scenario", [
    "high_press", "counterattack", "sustained_possession",
    "statsbomb_high_press",
])
def test_second_half_excerpt_has_explicit_roster_but_unknown_score_and_starters(scenario):
    data = client.get(f"/api/matches/{scenario}/presentation")
    assert data.status_code == 200
    profile = MatchPresentation.model_validate(data.json())
    assert profile.match_id == SyntheticReplaySource(scenario).load().manifest.match_id
    assert profile.source == "authored_fictional"
    assert profile.coverage == "excerpt"
    assert profile.home.starters is None and profile.away.starters is None
    assert not profile.initial_score_known
    assert profile.goals == () and profile.substitutions == ()
    assert profile.lineup_samples == ()
    assert len(profile.home.players) == len(profile.away.players) == 14


def test_complete_fixture_has_authored_start_and_exact_event_sourced_goal_state():
    data = SyntheticReplaySource("extended_match").load()
    response = client.get("/api/matches/extended_match/presentation")
    assert response.status_code == 200
    profile = MatchPresentation.model_validate(response.json())
    assert profile.match_id == data.manifest.match_id
    assert profile.coverage == "full_match" and profile.initial_score_known
    assert len(profile.home.starters or ()) == len(profile.away.starters or ()) == 11
    assert profile.home.team_id != profile.away.team_id
    assert profile.home.primary_color != profile.away.primary_color
    assert profile.home.emblem_text != profile.away.emblem_text
    assert profile.home.name == "Harbor FC" and profile.away.name == "Ridge FC"
    assert profile.home.players[0].surname != profile.away.team_id
    assert len(profile.goals) == 1
    goal = next(e for e in data.canonical_events if e.event_type == EventType.GOAL)
    frame = profile.goals[0]
    assert frame.event_id == goal.event_id
    assert frame.clock_ms == goal.clock_ms
    assert (frame.home, frame.away) == (
        (1, 0) if goal.team_id == profile.home.team_id else (0, 1)
    )
    assert goal.outcome == Outcome.SUCCESS
    assert [e.event_id for e in data.canonical_events if e.event_type == EventType.SHOT]
    assert not any(e.event_id == frame.event_id for e in data.canonical_events if e.event_type == EventType.SHOT)
    assert data.origin == FixtureOrigin.PITCHVOLT_SYNTHETIC


def test_authoritative_substitution_facts_have_reconciled_active_roster_and_actor_ids():
    source = SyntheticReplaySource("extended_match").load()
    profile = build_presentation("extended_match", source)
    assert len(profile.substitutions) == len(profile.lineup_samples) == 2
    previous_clock = 0
    for fact, snapshot in zip(profile.substitutions, profile.lineup_samples, strict=True):
        assert fact.clock_ms > previous_clock
        assert snapshot.clock_ms == fact.clock_ms
        assert fact.event_id == snapshot.event_id
        previous_clock = fact.clock_ms
        side = snapshot.home_active if fact.team_id == profile.home.team_id else snapshot.away_active
        assert fact.incoming_player_id in side
        assert fact.outgoing_player_id not in side
        assert len(snapshot.home_active) == len(snapshot.away_active) == 11
        team_events = [e for e in source.canonical_events if e.team_id == fact.team_id]
        assert any(
            e.clock_ms >= fact.clock_ms and e.player_id == fact.incoming_player_id
            for e in team_events
        )
        assert not any(
            e.clock_ms >= fact.clock_ms and e.player_id == fact.outgoing_player_id
            for e in team_events
        )


def test_substitution_actor_mapping_is_explicit_time_gated():
    data = SyntheticReplaySource("extended_match").load()
    for fact in authored_substitutions("extended_match", data.manifest.match_id):
        assert active_actor_id(
            fact.outgoing_player_id, fact.team_id, fact.clock_ms - 1,
            name="extended_match", match_id=data.manifest.match_id,
        ) == fact.outgoing_player_id
        assert active_actor_id(
            fact.outgoing_player_id, fact.team_id, fact.clock_ms,
            name="extended_match", match_id=data.manifest.match_id,
        ) == fact.incoming_player_id


def test_duplicate_roster_ids_or_numerical_shirts_rejected():
    team = build_presentation("extended_match", SyntheticReplaySource("extended_match").load()).home
    duplicate = list(team.players)
    duplicate[1] = duplicate[0]
    with pytest.raises(ValidationError, match="unique"):
        TeamPresentation(**{**team.model_dump(), "players": duplicate})
    bad = [p.model_dump() for p in team.players]
    bad[1]["jersey_number"] = bad[0]["jersey_number"]
    with pytest.raises(ValidationError, match="unique"):
        TeamPresentation(**{**team.model_dump(), "players": bad})
    with pytest.raises(ValidationError, match="exactly 11"):
        TeamPresentation(**{**team.model_dump(), "starters": [team.players[0].player_id] * 11})
    assert FictionalPlayer(player_id="custom-id", jersey_number=99, surname="Source").surname == "Source"


def test_invalid_goal_origin_or_missing_substitution_metadata_cannot_publish():
    synthetic = SyntheticReplaySource("extended_match").load()
    historical = replace(synthetic, manifest=synthetic.manifest.model_copy(update={
        "origin": FixtureOrigin.STATSBOMB_OPEN_DATA,
        "generator_seed": None, "source_url": "https://github.com/hudl/open-data/blob/pinned/data/events/123.json",
        "attribution": "StatsBomb Open Data",
    }), canonical_match=None, canonical_events=(), actions=(),
        omitted_by_type=(("fixture_boundary", synthetic.manifest.event_count),))
    with pytest.raises(ValueError, match="only canonical fictional"):
        build_presentation("extended_match", historical)
    assert client.get("/api/matches/unknown/presentation").status_code == 404
    with pytest.raises(ValidationError):
        SubstitutionFact(
            event_id="bad", team_id="harbor-fc", period=0,
            clock_ms=0, outgoing_player_id="harbor-1", incoming_player_id="harbor-12",
        )
