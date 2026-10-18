"""Optional atomic event+lineup acquisition from one pinned StatsBomb revision.

The default CLI mode is dry-run and never accesses the network. Original data
must stay local until the source's redistribution conditions are reviewed.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from urllib.request import urlopen

from pitchvolt.providers.statsbomb_360 import load_historical_360
from pitchvolt.providers.statsbomb_lineups import load_historical_lineups
from pitchvolt.statsbomb_acquire import prepare_fixture, source_urls
from pitchvolt.statsbomb_bundle_report import load_verified_historical_bundle

MAX_SOURCE_BYTES = 30_000_000


def pinned_bundle_urls(commit: str, match_id: str) -> tuple[str, str]:
    events_url, _ = source_urls(commit, match_id)
    return events_url, events_url.replace("/data/events/", "/data/lineups/")


def pinned_three_sixty_urls(commit: str, match_id: str) -> tuple[str, str, str]:
    """Pinned original assets must all come from the same match and revision."""
    events, lineups = pinned_bundle_urls(commit, match_id)
    return events, lineups, events.replace("/data/events/", "/data/three-sixty/")


def prepare_historical_bundle(
    events: bytes,
    lineups: bytes,
    *,
    commit: str,
    match_id: str,
    directory: Path,
    three_sixty: bytes | None = None,
) -> dict[str, str | int]:
    """Validate both inputs, then write exact bytes without leaving half a bundle."""
    source_urls(commit, match_id)
    if max(len(events), len(lineups), len(three_sixty or b"")) > MAX_SOURCE_BYTES:
        raise ValueError("Historical source exceeds 30 MB limit")
    if any((directory / name).exists() for name in (
        f"{match_id}.json", f"{match_id}.manifest.json", f"{match_id}.lineups.json",
        f"{match_id}.360.json",
    )):
        raise FileExistsError("Historical bundle already exists")
    digest = hashlib.sha256(lineups).hexdigest()
    frame_digest = hashlib.sha256(three_sixty).hexdigest() if three_sixty is not None else None
    temporary = directory / f"{match_id}.lineups.json"
    frame_path = directory / f"{match_id}.360.json"
    frames = None
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
        if three_sixty is not None and frame_digest is not None:
            frame_path.write_bytes(three_sixty)
            frames = load_historical_360(
                frame_path, report.fixture, expected_sha256=frame_digest
            )
    except Exception:
        temporary.unlink(missing_ok=True)
        frame_path.unlink(missing_ok=True)
        (directory / f"{match_id}.json").unlink(missing_ok=True)
        (directory / f"{match_id}.manifest.json").unlink(missing_ok=True)
        raise
    result: dict[str, str | int] = {
        "match_id": match_id,
        "upstream_commit": commit,
        "event_sha256": manifest.event_sha256,
        "lineup_sha256": digest,
        "event_count": report.identity.event_count,
        "projected_count": len(report.projection.actions),
    }
    if frames is not None and frame_digest is not None:
        result["frame_sha256"] = frame_digest
        result["frame_count"] = len(frames.frames)
        result["full_xi_frame_count"] = sum(
            item.has_observed_full_xi for item in frames.frames
        )
    return result


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
    parser.add_argument("--include-360", action="store_true",
                        help="Also acquire source-attested 360 frames for this match")
    args = parser.parse_args()
    events_url, lineups_url, frames_url = pinned_three_sixty_urls(
        args.commit, args.match_id
    )
    urls = (events_url, lineups_url, frames_url) if args.include_360 else (
        events_url, lineups_url
    )
    if not args.execute_download:
        print("DRY RUN; no download performed:", *urls)
        return
    events = _read_pinned(events_url)
    lineups = _read_pinned(lineups_url)
    frames = _read_pinned(frames_url) if args.include_360 else None
    print(prepare_historical_bundle(
        events, lineups,
        commit=args.commit, match_id=args.match_id, directory=args.output_dir,
        three_sixty=frames,
    ))


if __name__ == "__main__":
    main()
