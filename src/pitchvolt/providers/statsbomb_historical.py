"""Immutable, provenance-checked ingestion of historical StatsBomb Open Data JSON.

This module inspects original source records without projecting them into the
narrow synthetic-only MatchEvent model or silently discarding event families.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pitchvolt.fixture_manifest import FixtureManifest, FixtureOrigin

SUPPORTED_EVENT_TYPES = frozenset({"Pass", "Pressure", "Carry", "Shot", "Ball Recovery"})
PRESENTATION_EVENT_TYPES = frozenset({
    "Starting XI", "Substitution", "Half Start", "Half End",
    "Tactical Shift", "Bad Behaviour", "Player Off", "Player On",
})


@dataclass(frozen=True)
class HistoricalFixture:
    manifest: FixtureManifest
    records: tuple[dict[str, Any], ...]
    event_counts: dict[str, int]
    supported_count: int
    presentation_count: int
    unreviewed_count: int

    @property
    def coverage_complete_for_projection(self) -> bool:
        """False until every encountered family is reviewed for projection."""
        return self.unreviewed_count == 0


def _get_event_type(record: dict[str, Any]) -> str:
    value = record.get("type")
    if not isinstance(value, dict) or not isinstance(value.get("name"), str):
        raise TypeError("Historical event missing type.name")
    return value["name"]


def load_historical_fixture(path: Path, manifest: FixtureManifest) -> HistoricalFixture:
    """Read a pinned on-disk StatsBomb events file; no remote fetching or mutation.

    Reject malformed source files and invalid provenance. Preserve all records
    (including unreviewed event families) for audit; never imply that a subset
    constitutes a complete tactical or score reconstruction.
    """
    if manifest.origin != FixtureOrigin.STATSBOMB_OPEN_DATA:
        raise ValueError("Historical loader requires statsbomb_open_data origin")
    if path.name != f"{manifest.match_id}.json":
        raise ValueError("Source filename must agree with manifest match_id")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest.event_sha256:
        raise ValueError("StatsBomb event file SHA-256 mismatch")
    decoded = json.loads(raw)
    if not isinstance(decoded, list) or not decoded:
        raise ValueError("StatsBomb events must be a nonempty array")
    if len(decoded) != manifest.event_count:
        raise ValueError("StatsBomb event count mismatch")
    records: list[dict[str, Any]] = []
    types: Counter[str] = Counter()
    previous_index = 0
    ids: set[str] = set()
    for raw_event in decoded:
        if not isinstance(raw_event, dict):
            raise TypeError("StatsBomb event is not an object")
        index = raw_event.get("index")
        event_id = raw_event.get("id")
        if type(index) is not int or index <= previous_index:
            raise ValueError("StatsBomb event indices must be strictly increasing")
        if not isinstance(event_id, str) or not event_id or event_id in ids:
            raise ValueError("Missing or duplicate StatsBomb event ID")
        period = raw_event.get("period")
        if type(period) is not int or period < 1:
            raise ValueError("Invalid historical event period")
        if not isinstance(raw_event.get("timestamp"), str):
            raise TypeError("Historical event timestamp missing")
        previous_index = index
        ids.add(event_id)
        types[_get_event_type(raw_event)] += 1
        records.append(raw_event)
    supported = sum(n for kind, n in types.items() if kind in SUPPORTED_EVENT_TYPES)
    presentation = sum(n for kind, n in types.items() if kind in PRESENTATION_EVENT_TYPES)
    return HistoricalFixture(
        manifest=manifest,
        records=tuple(records),
        event_counts=dict(sorted(types.items())),
        supported_count=supported,
        presentation_count=presentation,
        unreviewed_count=len(records) - supported - presentation,
    )
