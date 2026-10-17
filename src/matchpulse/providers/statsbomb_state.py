"""Source-backed historical scoring observations and substitution ledger.

An excerpt's counted goals are not a match score. An unsupported own-goal
event invalidates complete-score eligibility rather than silently vanishing.
"""
from __future__ import annotations

from dataclasses import dataclass

from matchpulse.providers.statsbomb_bundle import validate_historical_bundle
from matchpulse.providers.statsbomb_historical import HistoricalFixture
from matchpulse.providers.statsbomb_lineups import HistoricalLineups


@dataclass(frozen=True)
class HistoricalGoal:
    event_id: str
    team_id: int


@dataclass(frozen=True)
class HistoricalSubstitution:
    event_id: str
    team_id: int
    outgoing_player_id: int
    incoming_player_id: int


@dataclass(frozen=True)
class HistoricalState:
    goals: tuple[HistoricalGoal, ...]
    substitutions: tuple[HistoricalSubstitution, ...]
    score_by_team: dict[int, int] | None
    score_unavailable_reason: str | None


def historical_event_state(
    fixture: HistoricalFixture, lineups: HistoricalLineups
) -> HistoricalState:
    """Only derive observations supported by independently verified input files."""
    report = validate_historical_bundle(fixture, lineups)
    goals: list[HistoricalGoal] = []
    substitutions: list[HistoricalSubstitution] = []
    unhandled_scoring = False
    for event in fixture.records:
        kind = event["type"]["name"]
        team_id = event["team"]["id"]
        if kind == "Shot":
            shot = event.get("shot")
            outcome = shot.get("outcome") if isinstance(shot, dict) else None
            if isinstance(outcome, dict) and outcome.get("name") == "Goal":
                goals.append(HistoricalGoal(event_id=event["id"], team_id=team_id))
            elif not isinstance(outcome, dict) or not isinstance(outcome.get("name"), str):
                # We cannot assert that an event with unknown outcome was not a goal.
                unhandled_scoring = True
        elif kind in {"Own Goal Against", "Own Goal For"}:
            # StatsBomb records may include both sides of an own-goal event.
            # Do not double count or infer which one is authoritative.
            unhandled_scoring = True
        elif kind == "Substitution":
            substitutions.append(HistoricalSubstitution(
                event_id=event["id"],
                team_id=team_id,
                outgoing_player_id=event["player"]["id"],
                incoming_player_id=event["substitution"]["replacement"]["id"],
            ))
    reason: str | None = None
    if fixture.manifest.event_coverage != "full_match":
        reason = "excerpt_without_authoritative_initial_score"
    elif unhandled_scoring:
        reason = "unresolved_scoring_event"
    elif not report.teams_consistent:
        reason = "incomplete_team_evidence"
    score = None if reason else {team_id: 0 for team_id in report.team_ids}
    if score is not None:
        for goal in goals:
            score[goal.team_id] += 1
    return HistoricalState(
        goals=tuple(goals),
        substitutions=tuple(substitutions),
        score_by_team=score,
        score_unavailable_reason=reason,
    )
