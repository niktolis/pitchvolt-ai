"""Offline, verified historical match bundle; never relabel source as synthetic.

Loads original file bytes against pinned provenance, reconciles source player
identities and constructs conservative pitch/action and event-state views.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from matchpulse.fixture_manifest import FixtureManifest
from matchpulse.providers.statsbomb_bundle import (
    HistoricalBundleReport,
    validate_historical_bundle,
)
from matchpulse.providers.statsbomb_historical import (
    HistoricalFixture,
    load_historical_fixture,
)
from matchpulse.providers.statsbomb_lineups import (
    HistoricalLineups,
    load_historical_lineups,
)
from matchpulse.providers.statsbomb_projection import (
    HistoricalProjection,
    project_historical_actions,
)
from matchpulse.providers.statsbomb_state import HistoricalState, historical_event_state


@dataclass(frozen=True)
class VerifiedHistoricalBundle:
    fixture: HistoricalFixture
    lineups: HistoricalLineups
    identity: HistoricalBundleReport
    projection: HistoricalProjection
    state: HistoricalState


def load_verified_historical_bundle(
    directory: Path, *, match_id: str, lineup_sha256: str
) -> VerifiedHistoricalBundle:
    """No network calls; SHA-pinned source data remains in the local directory."""
    if not match_id.isascii() or not match_id.isdecimal():
        raise ValueError("Expected numeric match ID")
    manifest_path = directory / f"{match_id}.manifest.json"
    manifest = FixtureManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    if manifest.match_id != match_id:
        raise ValueError("Manifest match ID disagrees with requested file")
    fixture = load_historical_fixture(directory / f"{match_id}.json", manifest)
    lineups = load_historical_lineups(
        directory / f"{match_id}.lineups.json", expected_sha256=lineup_sha256
    )
    identity = validate_historical_bundle(fixture, lineups)
    projection = project_historical_actions(fixture)
    state = historical_event_state(fixture, lineups)
    return VerifiedHistoricalBundle(
        fixture=fixture,
        lineups=lineups,
        identity=identity,
        projection=projection,
        state=state,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--match-id", required=True)
    parser.add_argument("--lineup-sha256", required=True)
    args = parser.parse_args()
    result = load_verified_historical_bundle(
        args.directory, match_id=args.match_id, lineup_sha256=args.lineup_sha256
    )
    print(json.dumps({
        "match_id": result.fixture.manifest.match_id,
        "origin": result.fixture.manifest.origin.value,
        "source_url": result.fixture.manifest.source_url,
        "attribution": result.fixture.manifest.attribution,
        "event_sha256": result.fixture.manifest.event_sha256,
        "lineup_sha256": result.lineups.sha256,
        "source_events": result.identity.event_count,
        "projected_actions": len(result.projection.actions),
        "omitted_actions_by_type": result.projection.omitted_by_type,
        "unknown_player_ids": result.identity.unknown_player_ids,
        "observed_goals": len(result.state.goals),
        "observed_substitutions": len(result.state.substitutions),
        "score_by_team": result.state.score_by_team,
        "score_unavailable_reason": result.state.score_unavailable_reason,
        "historical_ui_supported": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
