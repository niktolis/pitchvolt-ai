"""Do not invent historical scorelines or substitutions from partial files."""
from matchpulse.fixture_manifest import FixtureManifest, FixtureOrigin
from matchpulse.providers.statsbomb_historical import HistoricalFixture
from matchpulse.providers.statsbomb_lineups import HistoricalLineups, HistoricalPlayer, HistoricalTeam
from matchpulse.providers.statsbomb_state import historical_event_state


def case(*, coverage="full_match", own_goal=False):
    records = [
        {"id": "e1", "type": {"name": "Starting XI"}, "team": {"id": 1}},
        {"id": "e2", "type": {"name": "Shot"}, "team": {"id": 1},
         "player": {"id": 10}, "shot": {"outcome": {"name": "Goal"}}},
        {"id": "e3", "type": {"name": "Substitution"}, "team": {"id": 2},
         "player": {"id": 20}, "substitution": {"replacement": {"id": 21}}},
        {"id": "e4", "type": {"name": "Pass"}, "team": {"id": 2},
         "player": {"id": 21}},
    ]
    if own_goal:
        records.append({"id": "e5", "type": {"name": "Own Goal Against"},
                        "team": {"id": 2}, "player": {"id": 20}})
    manifest = FixtureManifest(
        fixture_id="hist-1", origin=FixtureOrigin.STATSBOMB_OPEN_DATA,
        match_id="1", event_sha256="a" * 64, event_count=len(records),
        match_duration_ms=5400000, event_coverage=coverage,
        source_url="https://github.com/hudl/open-data/blob/master/data/events/1.json",
        attribution="StatsBomb Open Data",
    )
    fixture = HistoricalFixture(manifest, tuple(records), {}, 0, 0, 0)
    player = lambda num: HistoricalPlayer(num, f"Player {num}", None, num, ())
    lineup = HistoricalLineups((
        HistoricalTeam(1, "Home", (player(10),)),
        HistoricalTeam(2, "Away", (player(20), player(21))),
    ), "b" * 64)
    return fixture, lineup


def test_explicit_goal_and_substitution_in_full_match():
    state = historical_event_state(*case())
    assert state.score_by_team == {1: 1, 2: 0}
    assert state.score_unavailable_reason is None
    assert [g.event_id for g in state.goals] == ["e2"]
    assert [(s.outgoing_player_id, s.incoming_player_id) for s in state.substitutions] == [(20, 21)]


def test_excerpt_keeps_observations_but_never_claims_zero_score():
    state = historical_event_state(*case(coverage="excerpt"))
    assert len(state.goals) == 1
    assert state.score_by_team is None
    assert state.score_unavailable_reason == "excerpt_without_authoritative_initial_score"


def test_own_goal_disables_claim_of_complete_score():
    state = historical_event_state(*case(own_goal=True))
    assert state.score_by_team is None
    assert state.score_unavailable_reason == "unresolved_scoring_event"


def test_unknown_shot_outcome_disables_complete_score():
    fixture, roster = case()
    fixture.records[1]["shot"] = {}
    state = historical_event_state(fixture, roster)
    assert state.goals == ()
    assert state.score_by_team is None
    assert state.score_unavailable_reason == "unresolved_scoring_event"
