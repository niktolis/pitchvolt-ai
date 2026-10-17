"""Optional atomic event+lineup acquisition from one pinned StatsBomb revision.

The default CLI mode is dry-run and never accesses the network. Original data
must stay local until the source's redistribution conditions are reviewed.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from urllib.request import urlopen

from matchpulse.providers.statsbomb_lineups import load_historical_lineups
from matchpulse.statsbomb_acquire import prepare_fixture, source_urls
from matchpulse.statsbomb_bundle_report import load_verified_historical_bundle

MAX_SOURCE_BYTES = 30_000_000


def pinned_bundle_urls(commit: str, match_id: str) -> tuple[str, str]:
    events_url, _ = source_urls(commit, match_id)
    return events_url, events_url.replace("/data/events/", "/data/lineups/")


def prepare_historical_bundle(
    events: bytes,
    lineups: bytes,
    *,
    commit: str,
    match_id: str,
    directory: Path,
) -> dict[str, str | int]:
    """Validate both inputs, then write exact bytes without leaving half a bundle."""
    source_urls(commit, match_id)
    if max(len(events), len(lineups)) > MAX_SOURCE_BYTES:
        raise ValueError("Historical source exceeds 30 MB limit")
    if any((directory / name).exists() for name in (
        f"{match_id}.json", f"{match_id}.manifest.json", f"{match_id}.lineups.json"
    )):
        raise FileExistsError("Historical bundle already exists")
    digest = hashlib.sha256(lineups).hexdigest()
    temporary = directory / f"{match_id}.lineups.json"
    # Check source-backed lineup shape before storing either document.
    directory.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(lineups)
    try:
        load_historical_lineups(temporary, expected_sha256=digest)
        manifest = prepare_fixture(
            events, commit=commit, match_id=match_id, directory=directory
        )
        report = load_verified_historical_bundle(
            directory, match_id=match_id, lineup_sha256=digest
        )
    except Exception:
        temporary.unlink(missing_ok=True)
        (directory / f"{match_id}.json").unlink(missing_ok=True)
        (directory / f"{match_id}.manifest.json").unlink(missing_ok=True)
        raise
    return {
        "match_id": match_id,
        "upstream_commit": commit,
        "event_sha256": manifest.event_sha256,
        "lineup_sha256": digest,
        "event_count": report.identity.event_count,
        "projected_count": len(report.projection.actions),
    }


def _read_pinned(url: str) -> bytes:
    with urlopen(url, timeout=30) as response:
        raw = response.read(MAX_SOURCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError("Historical source exceeds 30 MB limit")
    return raw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--match-id", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--execute-download", action="store_true")
    args = parser.parse_args()
    events_url, lineups_url = pinned_bundle_urls(args.commit, args.match_id)
    if not args.execute_download:
        print("DRY RUN; no download performed:", events_url, lineups_url)
        return
    events = _read_pinned(events_url)
    lineups = _read_pinned(lineups_url)
    print(prepare_historical_bundle(
        events, lineups,
        commit=args.commit, match_id=args.match_id, directory=args.output_dir,
    ))


if __name__ == "__main__":
    main()
