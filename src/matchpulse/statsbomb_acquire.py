"""Explicit, pinned and operator-run StatsBomb Open Data fixture acquisition.

No implicit network access; unit tests pass original JSON bytes to prepare_fixture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.request import urlopen

from matchpulse.fixture_manifest import FixtureManifest, FixtureOrigin
from matchpulse.providers.statsbomb_historical import load_historical_fixture

_COMMIT = re.compile(r"[0-9a-f]{40}")
_MATCH = re.compile(r"[0-9]+")
_ATTRIBUTION = "StatsBomb Open Data (Hudl/StatsBomb)"


def source_urls(commit: str, match_id: str) -> tuple[str, str]:
    """Construct fixed-repository URLs, never an arbitrary user-controlled host."""
    if not _COMMIT.fullmatch(commit) or not _MATCH.fullmatch(match_id):
        raise ValueError("Require lowercase 40-digit git commit and numeric match ID")
    suffix = f"data/events/{match_id}.json"
    return (
        f"https://raw.githubusercontent.com/hudl/open-data/{commit}/{suffix}",
        f"https://github.com/hudl/open-data/blob/{commit}/{suffix}",
    )


def prepare_fixture(
    content: bytes, *, commit: str, match_id: str, directory: Path
) -> FixtureManifest:
    """Validate before storing exactly received bytes and a separate manifest."""
    _, source = source_urls(commit, match_id)
    parsed = json.loads(content)
    if not isinstance(parsed, list) or not parsed:
        raise ValueError("Expected nonempty StatsBomb events array")
    last_clock = 0
    for record in parsed:
        if not isinstance(record, dict):
            raise TypeError("Invalid StatsBomb event")
        minute = record.get("minute")
        second = record.get("second")
        if type(minute) is not int or type(second) is not int or minute < 0 or not 0 <= second < 60:
            raise ValueError("Historical event minute/second invalid")
        last_clock = max(last_clock, (minute * 60 + second) * 1000)
    if not last_clock:
        raise ValueError("Fixture has no positive match clock")
    manifest = FixtureManifest(
        fixture_id=f"statsbomb-{match_id}-{commit[:12]}",
        origin=FixtureOrigin.STATSBOMB_OPEN_DATA,
        match_id=match_id,
        event_sha256=hashlib.sha256(content).hexdigest(),
        event_count=len(parsed),
        match_duration_ms=last_clock,
        event_coverage="full_match" if all(
            any(
                isinstance(e, dict) and isinstance(e.get("type"), dict)
                and e["type"].get("name") == "Half End" and e.get("period") == period
                for e in parsed
            ) for period in (1, 2)
        ) else "excerpt",
        source_url=source,
        attribution=_ATTRIBUTION,
    )
    # Round-trip through the existing strict historical boundary before writing.
    # All files are dedicated to a match; never overwrite a previous acquisition.
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{match_id}.json"
    meta = directory / f"{match_id}.manifest.json"
    if target.exists() or meta.exists():
        raise FileExistsError("Existing fixture requires explicit cleanup before reacquiring")
    try:
        target.write_bytes(content)
        load_historical_fixture(target, manifest)
        meta.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    except Exception:
        target.unlink(missing_ok=True)
        meta.unlink(missing_ok=True)
        raise
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True, help="Full 40-character upstream commit SHA")
    parser.add_argument("--match-id", required=True, help="Numeric StatsBomb match ID")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--execute-download", action="store_true", help="Explicit network opt-in")
    args = parser.parse_args()
    remote, _ = source_urls(args.commit, args.match_id)
    if not args.execute_download:
        print("Dry run: would fetch", remote)
        return
    with urlopen(remote, timeout=30) as response:
        raw = response.read(30_000_001)
    if len(raw) > 30_000_000:
        raise ValueError("Fixture exceeds bounded 30 MB limit")
    manifest = prepare_fixture(
        raw, commit=args.commit, match_id=args.match_id, directory=args.output_dir
    )
    print(manifest.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
