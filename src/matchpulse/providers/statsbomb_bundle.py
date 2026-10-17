"""Cross-file identity checks for pinned historical StatsBomb match data.

The event and lineup loaders validate files independently. This seam links
their *source identifiers* without inventing starters or canonical events.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from matchpulse.providers.statsbomb_historical import HistoricalFixture
from matchpulse.providers.statsbomb_lineups import HistoricalLineups


@dataclass(frozen=True)
class HistoricalBundleReport:
    event_count: int
    team_ids: tuple[int, int]
    lineup_player_count: int
    referenced_player_count: int
    unknown_player_ids: tuple[int, ...]
    missing_player_references: int
    source_substitution_count: int
    teams_consistent: bool
    roster_coverage_complete: bool


def validate_historical_bundle(
    fixture: HistoricalFixture, lineups: HistoricalLineups
) -> HistoricalBundleReport:
    """Inspect exact numeric event identity against separately verified lineups.

    Fail on unknown event teams and contradictory player->team attribution.
    Other player gaps are disclosed rather than silently assigning a name.
    No inference of an XI, goal, score or substitution effect is performed.
    """
    teams = {team.team_id: team for team in lineups.teams}
    if len(teams) != 2:
        raise ValueError("Historical bundle requires two distinct teams")
    player_teams: dict[int, int] = {}
    for team in lineups.teams:
        for player in team.players:
            previous = player_teams.setdefault(player.player_id, team.team_id)
            if previous != team.team_id:
                raise ValueError("Historical lineup assigns player to multiple teams")
    unknown: set[int] = set()
    referenced: set[int] = set()
    missing = 0
    substitutions = 0
    counts: Counter[int] = Counter()
    for event in fixture.records:
        team = event.get("team")
        team_id = team.get("id") if isinstance(team, dict) else None
        if type(team_id) is not int or team_id not in teams:
            raise ValueError("Historical event references an unknown team")
        counts[team_id] += 1
        kind = event["type"]["name"]
        if kind == "Substitution":
            substitutions += 1
        player = event.get("player")
        if player is None:
            missing += 1
            continue
        player_id = player.get("id") if isinstance(player, dict) else None
        if type(player_id) is not int or player_id <= 0:
            raise ValueError("Historical event player ID is invalid")
        referenced.add(player_id)
        if player_id not in player_teams:
            unknown.add(player_id)
        elif player_teams[player_id] != team_id:
            raise ValueError("Historical event player belongs to opposing team")
        if kind == "Substitution":
            replacement = event.get("substitution")
            if not isinstance(replacement, dict) or not isinstance(replacement.get("replacement"), dict):
                raise ValueError("Historical substitution lacks replacement identity")
            replacement_id = replacement["replacement"].get("id")
            if type(replacement_id) is not int or replacement_id <= 0:
                raise ValueError("Invalid historical substitute ID")
            referenced.add(replacement_id)
            if replacement_id not in player_teams:
                unknown.add(replacement_id)
            elif player_teams[replacement_id] != team_id:
                raise ValueError("Historical substitute belongs to opposing team")
    return HistoricalBundleReport(
        event_count=len(fixture.records),
        team_ids=tuple(sorted(teams)),
        lineup_player_count=len(player_teams),
        referenced_player_count=len(referenced),
        unknown_player_ids=tuple(sorted(unknown)),
        missing_player_references=missing,
        source_substitution_count=substitutions,
        teams_consistent=all(counts.values()) and len(counts) == 2,
        roster_coverage_complete=not unknown,
    )
