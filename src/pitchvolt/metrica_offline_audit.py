"""Read-only, SHA-pinned offline audit of Metrica's anonymized CSV sample games.

No downloader, HTTP client, source file copy, public API, player tracking endpoint,
or license grant is implemented here. Original files remain entirely operator-local.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

_REPOSITORY = "https://github.com/metrica-sports/sample-data"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
# Canonical git objects from the exact public Metrica commit tree, queried
# by GitHub Git Trees API. Git blob OIDs bind the bytes to THAT revision;
# an operator-provided SHA-256 checksum alone cannot establish origin.
_UPSTREAM_COMMIT = "e706dd506b360d69d9d123d5b8026e7294b13996"
_UPSTREAM_BLOBS = {
    1: {
        "Home": ("ce2e91c0e633426cec1146f4e728b72417454e3d", 32782961),
        "Away": ("ff409a5680fd75acc7cebcf786827214c687478b", 32782073),
        "Events": ("3c426dd4f442dd433bccf89e3634f91aa310cd8f", 139446),
    },
    2: {
        "Home": ("8b4d3648888cc8b033e7142919ebaea04f6328e0", 31890338),
        "Away": ("e7334d8d762954a215c49e55f211855000243fdc", 29627711),
        "Events": ("decccd47c1d53960d290cb6679337eec83a8a97f", 153897),
    },
}
_EVENT_FIELDS = {
    "Team", "Type", "Period", "Start Frame", "Start Time [s]", "From",
}


def upstream_path(game: int, kind: str, *, commit: str) -> str:
    """Fixed paths for game 1/2 only; no arbitrary host or unpinned upstream."""
    if game not in (1, 2) or kind not in ("Home", "Away", "Events"):
        raise ValueError("Only Metrica sample games 1/2 and Home/Away/Events supported")
    if not _COMMIT.fullmatch(commit):
        raise ValueError("A full lower-case 40-digit upstream commit is mandatory")
    stem = f"data/Sample_Game_{game}/Sample_Game_{game}_Raw"
    suffix = "EventsData.csv" if kind == "Events" else f"TrackingData_{kind}_Team.csv"
    return f"{_REPOSITORY}/blob/{commit}/{stem}{suffix}"


def _verify_source_bytes(
    path: Path, expected_sha256: str, expected_git_oid: str, expected_size: int,
) -> str:
    """Verify local checksum AND the canonical Git blob identity in one pass."""
    if not _SHA.fullmatch(expected_sha256):
        raise ValueError("Expected SHA-256 must be 64 lower-case hexadecimal characters")
    if not _COMMIT.fullmatch(expected_git_oid) or expected_size < 0:
        raise ValueError("Invalid pinned upstream blob metadata")
    size = path.stat().st_size
    if size != expected_size:
        raise ValueError(f"Upstream pinned file size mismatch for {path.name}")
    sha256 = hashlib.sha256()
    git_blob = hashlib.sha1()
    git_blob.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            sha256.update(chunk)
            git_blob.update(chunk)
    if sha256.hexdigest() != expected_sha256:
        raise ValueError(f"SHA-256 mismatch for {path.name}")
    if git_blob.hexdigest() != expected_git_oid:
        raise ValueError(f"Upstream Git blob mismatch for {path.name}")
    return sha256.hexdigest()


def _coordinate(token: str) -> str:
    """Do not clamp genuine out-of-bounds detections or invent null positions."""
    if token.strip().lower() in ("", "nan"):
        return "missing"
    try:
        value = float(token)
    except ValueError as error:
        raise ValueError("Malformed tracking coordinate") from error
    if not math.isfinite(value):
        raise ValueError("Nonfinite tracking coordinate")
    return "observed" if 0 <= value <= 1 else "outside_field"


def _point(x: str, y: str) -> str:
    statuses = (_coordinate(x), _coordinate(y))
    if "missing" in statuses:
        if statuses != ("missing", "missing"):
            raise ValueError("Incomplete tracking x/y pair")
        return "missing"
    if "outside_field" in statuses:
        return "outside_field"
    return "observed"


def _tracking_header(reader: Any, team: str) -> tuple[int, tuple[str, ...]]:
    meta = next(reader, None)
    jerseys = next(reader, None)
    fields = next(reader, None)
    if not meta or not jerseys or not fields:
        raise ValueError("Metrica tracking requires three CSV header rows")
    count = len(fields)
    if count < 7 or (count - 5) % 2 or len(jerseys) != count:
        raise ValueError("Tracking coordinate columns must form player pairs plus ball x/y")
    if [v.strip().lower() for v in fields[:3]] != ["period", "frame", "time [s]"]:
        raise ValueError("Unexpected Metrica period/frame/time header")
    if not any(team.lower() == value.strip().lower() for value in meta):
        raise ValueError("Tracking file team header mismatch")
    if "ball" not in {fields[-2].strip().lower(), jerseys[-2].strip().lower()}:
        raise ValueError("Tracking ball x/y channels not declared")
    identifiers = tuple(jerseys[i].strip() for i in range(3, count - 2, 2))
    if not all(identifiers) or len(identifiers) != len(set(identifiers)):
        raise ValueError("Player jersey identifiers must be distinct and nonempty")
    return count, identifiers


def _tracking_sample(path: Path, *, team: str, max_frames: int) -> dict[str, Any]:
    if max_frames < 2 or max_frames > 5000:
        raise ValueError("Local inspection must use 2..5000 rows")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        width, jerseys = _tracking_header(reader, team)
        timestamps: list[tuple[int, int, float]] = []
        coverage = {"observed": 0, "missing": 0, "outside_field": 0}
        ball = dict.fromkeys(coverage, 0)
        visible_counts: list[int] = []
        previous_frame = -1
        for row in reader:
            if len(timestamps) >= max_frames:
                break
            if not row:
                continue
            if len(row) != width:
                raise ValueError("Tracking row width does not match header")
            period = int(row[0])
            frame = int(row[1])
            timestamp = float(row[2])
            if period not in (1, 2) or frame <= previous_frame or not math.isfinite(timestamp):
                raise ValueError("Invalid/unsorted Metrica period, frame or time")
            if timestamp < 0 or abs(frame / 25 - timestamp) > 0.08:
                raise ValueError("Tracking frame/time mismatch (expected 25 Hz)")
            previous_frame = frame
            count = 0
            for i in range(3, width - 2, 2):
                kind = _point(row[i], row[i + 1])
                coverage[kind] += 1
                if kind == "observed":
                    count += 1
            ball[_point(row[-2], row[-1])] += 1
            visible_counts.append(count)
            timestamps.append((period, frame, timestamp))
    if len(timestamps) < 2:
        raise ValueError("Tracking sample contains fewer than two frames")
    return {
        "team": team,
        "player_slots": len(jerseys),
        "frames_examined": len(timestamps),
        "player_samples": coverage,
        "ball_samples": ball,
        "visible_players_min": min(visible_counts),
        "visible_players_max": max(visible_counts),
        "_times": timestamps,
    }


def _event_audit(path: Path, frames: set[tuple[int, int]]) -> dict[str, Any]:
    matches = 0
    checked = 0
    types: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not _EVENT_FIELDS.issubset(reader.fieldnames):
            raise ValueError("Metrica events header missing event/frame fields")
        for event in reader:
            if event["Team"] not in ("Home", "Away"):
                raise ValueError("Unexpected Metrica event team")
            period = int(event["Period"])
            frame = int(event["Start Frame"])
            timestamp = float(event["Start Time [s]"])
            if (period not in (1, 2) or frame < 0
                    or not math.isfinite(timestamp) or timestamp < 0):
                raise ValueError("Invalid Metrica event period/frame/time")
            if frame > 0 and abs(frame / 25 - timestamp) > 0.08:
                raise ValueError("Event frame/time mismatch")
            checked += 1
            types.add(event["Type"])
            matches += int((period, frame) in frames)
    if not checked:
        raise ValueError("Metrica source has no events")
    return {
        "events_examined": checked,
        "event_types": sorted(types),
        "events_with_examined_tracking_frame": matches,
    }


def inspect_game(
    directory: Path,
    *,
    game: int,
    commit: str,
    expected_sha256: dict[str, str],
    max_frames: int = 250,
    _test_git_blob_manifest: dict[str, tuple[str, int]] | None = None,
) -> dict[str, Any]:
    """Offline audit; bind real source bytes to canonical upstream Git objects.

    The private test override is used only by synthetic unit fixtures; reports
    from test-overridden manifests are NEVER marked as upstream verified.
    """
    if commit != _UPSTREAM_COMMIT:
        raise ValueError("Only the audited immutable upstream commit is supported")
    filenames = {
        kind: f"Sample_Game_{game}_Raw" + (
            "EventsData.csv" if kind == "Events" else f"TrackingData_{kind}_Team.csv"
        )
        for kind in ("Home", "Away", "Events")
    }
    urls = {kind: upstream_path(game, kind, commit=commit) for kind in filenames}
    if set(expected_sha256) != set(filenames):
        raise ValueError("Exactly Home, Away, Events SHA-256 pins required")
    if directory.name != f"Sample_Game_{game}":
        raise ValueError("Directory name must identify the same Metrica sample game")
    manifest = (
        _UPSTREAM_BLOBS[game]
        if _test_git_blob_manifest is None else _test_git_blob_manifest
    )
    if set(manifest) != set(filenames):
        raise ValueError("Canonical upstream source manifest is incomplete")
    verified = {
        kind: _verify_source_bytes(
            directory / name, expected_sha256[kind], *manifest[kind],
        )
        for kind, name in filenames.items()
    }
    home = _tracking_sample(directory / filenames["Home"], team="Home", max_frames=max_frames)
    away = _tracking_sample(directory / filenames["Away"], team="Away", max_frames=max_frames)
    times_home = home.pop("_times")
    times_away = away.pop("_times")
    if times_home != times_away:
        raise ValueError("Home/Away frame and timestamp sequences are not synchronized")
    events = _event_audit(directory / filenames["Events"], {(t[0], t[1]) for t in times_home})
    return {
        "origin": "metrica_sample_csv_offline",
        "source_commit": commit,
        "game": game,
        "canonical_upstream_blob_identity_verified": _test_git_blob_manifest is None,
        "source_files": {
            kind: {
                "url": urls[kind],
                "sha256": verified[kind],
                "git_blob_oid": manifest[kind][0],
                "verified_bytes": manifest[kind][1],
            }
            for kind in filenames
        },
        "frame_rate_hz": 25,
        "teams": {"Home": home, "Away": away},
        "events": events,
        "tracking_frames_synchronized": True,
        "events_joined_to_sample": events["events_with_examined_tracking_frame"] > 0,
        "license_status": "UNVERIFIED_DO_NOT_REDISTRIBUTE",
        "may_publish_source_data": False,
        "may_serve_tracking_replay": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--game", required=True, type=int, choices=[1, 2])
    parser.add_argument("--commit", required=True)
    parser.add_argument("--home-sha256", required=True)
    parser.add_argument("--away-sha256", required=True)
    parser.add_argument("--events-sha256", required=True)
    parser.add_argument("--max-frames", type=int, default=250)
    args = parser.parse_args()
    report = inspect_game(
        args.directory,
        game=args.game,
        commit=args.commit,
        expected_sha256={
            "Home": args.home_sha256,
            "Away": args.away_sha256,
            "Events": args.events_sha256,
        },
        max_frames=args.max_frames,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
