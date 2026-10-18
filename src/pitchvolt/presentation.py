"""Authoritative *fictional* match presentation; no invented spatial tracking.

Team identities/rosters and substitutions are explicit authored fixture facts.
Score is event-sourced from validated canonical GOAL events, never calculated
from a shot outcome, possession, UI counter, or model-generated narrative.
"""
from __future__ import annotations

from itertools import pairwise
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pitchvolt.events import EventType, MatchMetadata
from pitchvolt.extended_fixtures import EXTENDED_SCENARIO
from pitchvolt.fixture_manifest import FixtureOrigin
from pitchvolt.replay_dataset import ReplayDataset

COLORS = {"harbor-fc": ("#47b5db", "#0c3852"), "ridge-fc": ("#ed765b", "#642a31")}
# Fictional surnames are deliberately authored; never inferred from jersey IDs.
SURNAMES = (
    "Marlow", "Voss", "Ellery", "Fenwick", "Orlan", "Kestrel", "Tarn",
    "Calder", "Lowen", "Merrin", "Ashby", "Wren", "Sorel", "Halden",
)
SUBSTITUTION_SPECS = (
    (3_660_000, "harbor-fc", "harbor-11", "harbor-12"),
    (3_900_000, "ridge-fc", "ridge-10", "ridge-12"),
)


class FictionalPlayer(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    player_id: str = Field(min_length=1)
    surname: str = Field(min_length=1)
    jersey_number: int = Field(ge=1, le=99)


class TeamPresentation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    team_id: str
    name: str
    abbreviation: str
    primary_color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    secondary_color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    emblem_text: str = Field(min_length=1, max_length=3)
    coach: str
    players: tuple[FictionalPlayer, ...]
    starters: tuple[str, ...] | None = None

    @model_validator(mode="after")
    def unique_players(self) -> TeamPresentation:
        ids = [p.player_id for p in self.players]
        shirts = [p.jersey_number for p in self.players]
        if len(ids) != len(set(ids)) or len(shirts) != len(set(shirts)):
            raise ValueError("Roster identities and jersey numbers must be unique")
        if self.starters is not None and (
            len(self.starters) != 11 or len(set(self.starters)) != 11
            or not set(self.starters).issubset(ids)
        ):
            raise ValueError("Source-authoritative starting XI must be exactly 11 roster IDs")
        return self


class SubstitutionFact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    event_id: str = Field(min_length=1)
    team_id: str
    period: int = Field(ge=1, le=2)
    clock_ms: int = Field(ge=0)
    outgoing_player_id: str
    incoming_player_id: str


class ScoreSample(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    event_id: str
    period: int = Field(ge=1, le=2)
    clock_ms: int = Field(ge=0)
    home: int = Field(ge=0)
    away: int = Field(ge=0)


class LineupSample(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    event_id: str
    clock_ms: int = Field(ge=0)
    home_active: tuple[str, ...]
    away_active: tuple[str, ...]


class MatchPresentation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    match_id: str
    source: Literal["authored_fictional"] = "authored_fictional"
    coverage: Literal["full_match", "excerpt"]
    home: TeamPresentation
    away: TeamPresentation
    initial_score_known: bool
    goals: tuple[ScoreSample, ...]
    substitutions: tuple[SubstitutionFact, ...]
    lineup_samples: tuple[LineupSample, ...]


def _team(team_id: str, *, starters_known: bool) -> TeamPresentation:
    if team_id not in COLORS:
        raise ValueError("Unknown fictional team in match metadata")
    short = "Harbor" if team_id == "harbor-fc" else "Ridge"
    code = "HFC" if team_id == "harbor-fc" else "RFC"
    prefix = "harbor" if team_id == "harbor-fc" else "ridge"
    color, secondary = COLORS[team_id]
    return TeamPresentation(
        team_id=team_id, name=f"{short} FC", abbreviation=code,
        primary_color=color, secondary_color=secondary, emblem_text=code,
        coach="Mira Vale" if prefix == "harbor" else "Elias North",
        players=tuple(
            FictionalPlayer(
                player_id=f"{prefix}-{number}",
                surname=SURNAMES[(number - 1) % len(SURNAMES)],
                jersey_number=number,
            ) for number in range(1, 15)
        ),
        starters=tuple(f"{prefix}-{i}" for i in range(1, 12))
        if starters_known else None,
    )


def authored_substitutions(name: str, match_id: str) -> tuple[SubstitutionFact, ...]:
    """Explicit, fixed synthetic fixture facts; never inferred from actor changes."""
    if name != EXTENDED_SCENARIO:
        return ()
    return tuple(
        SubstitutionFact(
            event_id=f"{match_id}-sub-{i}", clock_ms=ms, period=2,
            team_id=team, outgoing_player_id=out, incoming_player_id=on,
        )
        for i, (ms, team, out, on) in enumerate(SUBSTITUTION_SPECS, 1)
    )


def active_actor_id(
    player_id: str, team_id: str, clock_ms: int, *, name: str, match_id: str
) -> str:
    """Explicit fictional substitution mapping, not position/lineup inference."""
    for change in authored_substitutions(name, match_id):
        if (
            clock_ms >= change.clock_ms and team_id == change.team_id
            and player_id == change.outgoing_player_id
        ):
            return change.incoming_player_id
    return player_id


def build_presentation(name: str, dataset: ReplayDataset) -> MatchPresentation:
    if dataset.origin != FixtureOrigin.PITCHVOLT_SYNTHETIC or not dataset.permits_tactical_processing:
        raise ValueError("Published presentation accepts only canonical fictional fixtures")
    match: MatchMetadata | None = dataset.canonical_match
    if match is None:
        raise ValueError("Missing canonical match identity")
    full = dataset.manifest.event_coverage == "full_match"
    home = _team(match.home_team_id, starters_known=full)
    away = _team(match.away_team_id, starters_known=full)
    teams = {home.team_id: home, away.team_id: away}
    replacements = authored_substitutions(name, match.match_id)
    if any(
        b.clock_ms <= a.clock_ms or b.event_id == a.event_id
        for a, b in pairwise(replacements)
    ):
        raise ValueError("Substitution source events must be unique and ordered")
    if any(item.clock_ms > dataset.manifest.match_duration_ms for item in replacements):
        raise ValueError("Substitutions cannot occur after the match ends")
    if not full and replacements:
        raise ValueError("Cannot infer lineup changes inside incomplete excerpt")
    # Score starts at authored synthetic kickoff only for complete source coverage.
    score_home = score_away = 0
    goal_samples: list[ScoreSample] = []
    for event in dataset.canonical_events:
        if event.event_type != EventType.GOAL:
            continue
        if full:
            if event.team_id == home.team_id:
                score_home += 1
            else:
                score_away += 1
            goal_samples.append(ScoreSample(
                event_id=event.event_id, period=event.period,
                clock_ms=event.clock_ms, home=score_home, away=score_away,
            ))
    lineups: list[LineupSample] = []
    if full:
        assert home.starters is not None and away.starters is not None
        live = {home.team_id: list(home.starters), away.team_id: list(away.starters)}
        for fact in replacements:
            if fact.team_id not in teams:
                raise ValueError("Unknown substitution team")
            team = teams[fact.team_id]
            starters = live[fact.team_id]
            if (fact.outgoing_player_id not in starters
                    or fact.incoming_player_id in starters
                    or fact.incoming_player_id not in {p.player_id for p in team.players}):
                raise ValueError("Invalid explicit substitution: outgoing/bench mismatch")
            for event in dataset.canonical_events:
                if (
                    event.team_id == fact.team_id and event.clock_ms >= fact.clock_ms
                    and event.player_id == fact.outgoing_player_id
                ):
                    raise ValueError("Substituted player still appears in later fixture events")
            starters[starters.index(fact.outgoing_player_id)] = fact.incoming_player_id
            lineups.append(LineupSample(
                event_id=fact.event_id, clock_ms=fact.clock_ms,
                home_active=tuple(live[home.team_id]),
                away_active=tuple(live[away.team_id]),
            ))
        for event in dataset.canonical_events:
            team = teams[event.team_id]
            if event.player_id not in {p.player_id for p in team.players}:
                raise ValueError("Unknown fictional event actor")
            active_ids = (
                home.starters if event.team_id == home.team_id else away.starters
            )
            for state in lineups:
                if state.clock_ms <= event.clock_ms:
                    active_ids = state.home_active if event.team_id == home.team_id else state.away_active
            if event.player_id not in active_ids:
                raise ValueError("Event actor absent from explicitly authored lineup")
    else:
        for event in dataset.canonical_events:
            if event.player_id not in {p.player_id for p in teams[event.team_id].players}:
                raise ValueError("Excerpt actor missing from declared fictional roster")

    return MatchPresentation(
        match_id=match.match_id, coverage=dataset.manifest.event_coverage,
        home=home, away=away, initial_score_known=full,
        goals=tuple(goal_samples), substitutions=replacements,
        lineup_samples=tuple(lineups),
    )
