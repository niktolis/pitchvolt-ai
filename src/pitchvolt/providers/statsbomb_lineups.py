"""Lossless source-backed roster index for StatsBomb historical fixtures.

A roster is display metadata, not a synthetic team identity or an inferred
starting XI. Starting status requires explicit lineup positions or Starting XI
events; the loader does not invent an eleven from a listed squad.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HistoricalPlayer:
    player_id: int
    name: str
    nickname: str | None
    jersey_number: int | None
    positions: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalTeam:
    team_id: int
    name: str
    players: tuple[HistoricalPlayer, ...]


@dataclass(frozen=True)
class HistoricalLineups:
    teams: tuple[HistoricalTeam, ...]
    sha256: str


def _positive_id(value: Any, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"Invalid {label}")
    return value


def _name(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid {label}")
    return value


def load_historical_lineups(path: Path, *, expected_sha256: str) -> HistoricalLineups:
    """Validate the original file bytes before mapping roster presentation."""
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError("Historical lineup SHA-256 mismatch")
    items = json.loads(raw)
    if not isinstance(items, list) or len(items) != 2:
        raise ValueError("Expected exactly two historical match teams")
    teams: list[HistoricalTeam] = []
    seen_teams: set[int] = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("lineup"), list):
            raise TypeError("Invalid historical team lineup")
        team_id = _positive_id(item.get("team_id"), "team ID")
        if team_id in seen_teams:
            raise ValueError("Duplicate team ID")
        seen_teams.add(team_id)
        seen_players: set[int] = set()
        players: list[HistoricalPlayer] = []
        for player in item["lineup"]:
            if not isinstance(player, dict):
                raise TypeError("Invalid historical player")
            player_id = _positive_id(player.get("player_id"), "player ID")
            if player_id in seen_players:
                raise ValueError("Duplicate player ID within a team")
            seen_players.add(player_id)
            jersey = player.get("jersey_number")
            if jersey is not None and (type(jersey) is not int or jersey < 0):
                raise ValueError("Invalid jersey number")
            nickname = player.get("player_nickname")
            if nickname is not None and not isinstance(nickname, str):
                raise TypeError("Invalid player nickname")
            positions = player.get("positions", [])
            if not isinstance(positions, list):
                raise TypeError("Invalid player positions")
            names = tuple(
                _name(p.get("position"), "position")
                for p in positions
                if isinstance(p, dict) and p.get("position") is not None
            )
            players.append(HistoricalPlayer(
                player_id=player_id,
                name=_name(player.get("player_name"), "player name"),
                nickname=nickname,
                jersey_number=jersey,
                positions=names,
            ))
        teams.append(HistoricalTeam(
            team_id=team_id,
            name=_name(item.get("team_name"), "team name"),
            players=tuple(players),
        ))
    return HistoricalLineups(teams=tuple(teams), sha256=digest)
