"""Offline IDSSE/DFL Sportec source verification for one authentic match.

Phase 1 validates source identifiers and XML metadata/event integrity.
It does NOT infer trajectories, synchronize event time or publish tracking
samples. Source files must be explicitly downloaded at the pinned revision.
No network or optional parser dependency is used by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree

MATCH_ID = "J03WMX"
DFL_MATCH_ID = "DFL-MAT-J03WMX"
REPOSITORY = "pysport/idsse-data"
REVISION = "a715a38dfbaf5f58e431727c2b78d174101a703c"
TRACKING_SHA256 = "d3dd92e509421a6466acb0a083c009035f1751bc5fd9ef42ffa8f20d01cf7d49"
SOURCE_NAMES = {
    "metadata": "DFL_02_01_matchinformation_DFL-COM-000001_DFL-MAT-J03WMX.xml",
    "events": "DFL_03_02_events_raw_DFL-COM-000001_DFL-MAT-J03WMX.xml",
    "tracking": "DFL_04_03_positions_raw_observed_DFL-COM-000001_DFL-MAT-J03WMX.xml",
}
CHECKSUM = re.compile(r"[a-f0-9]{64}\Z")
MAX_SMALL_XML_BYTES = 8 * 1024 * 1024


def source_url(kind: str) -> str:
    """Immutable, exact-match dataset URL. Never use a mutable main branch."""
    return (
        f"https://huggingface.co/datasets/{REPOSITORY}/resolve/{REVISION}/"
        f"{SOURCE_NAMES[kind]}"
    )


def sha256_file(path: Path, expected: str) -> tuple[str, int]:
    """Stream hash instead of loading a 419 MB XML source into Python memory."""
    if not CHECKSUM.fullmatch(expected):
        raise ValueError("An exact lower-case 64-character SHA-256 is required")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as content:
        for block in iter(lambda: content.read(1024 * 1024), b""):
            size += len(block)
            digest.update(block)
    if digest.hexdigest() != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}")
    return digest.hexdigest(), size


def _xml_from_verified_bytes(path: Path, expected_sha: str) -> ElementTree.Element:
    """Reject entities/DTDs, malformed XML and excessive small-file input."""
    if path.stat().st_size > MAX_SMALL_XML_BYTES:
        raise ValueError(f"Small IDSSE XML input too large: {path.name}")
    # All original sources use this format; no external entities or DTD needed.
    data = path.read_bytes()
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("Unsafe XML entity declaration")
    if hashlib.sha256(data).hexdigest() != expected_sha:
        raise ValueError(f"SHA-256 mismatch for {path.name}")
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Malformed IDSSE XML: {path.name}") from exc
    if root.tag.rsplit("}", 1)[-1] != "PutDataRequest":
        raise ValueError("Unexpected IDSSE XML root")
    return root


def _tag(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _match_metadata(root: ElementTree.Element) -> dict[str, object]:
    general = next((e for e in root.iter() if _tag(e) == "General"), None)
    environment = next((e for e in root.iter() if _tag(e) == "Environment"), None)
    teams = [e for e in root.iter() if _tag(e) == "Team"]
    if general is None or environment is None or len(teams) != 2:
        raise ValueError("IDSSE metadata missing General, pitch or exactly two teams")
    if general.get("MatchId") != DFL_MATCH_ID:
        raise ValueError("IDSSE metadata cross-match identity mismatch")
    if general.get("HomeTeamName") != "1. FC Köln":
        raise ValueError("Unexpected IDSSE home team in pinned match")
    if general.get("GuestTeamName") != "FC Bayern München":
        raise ValueError("Unexpected IDSSE away team in pinned match")
    try:
        length, width = float(environment.attrib["PitchX"]), float(environment.attrib["PitchY"])
    except (KeyError, ValueError) as error:
        raise ValueError("Invalid source-authoritative pitch dimensions") from error
    if length != 105 or width != 68:
        raise ValueError("Source pitch dimensions require explicit adapter review")
    identities = [team.get("TeamId") for team in teams]
    if len(set(identities)) != 2 or any(not identity for identity in identities):
        raise ValueError("Missing or repeated team identifiers")
    if set(identities) != {general.get("HomeTeamId"), general.get("GuestTeamId")}:
        raise ValueError("Registered teams do not match match-header team IDs")
    # Presence/uniqueness only: no 11/11 positional coverage is inferred here.
    players: dict[str, int] = {}
    for team in teams:
        entries = [e for e in team.iter() if _tag(e) == "Player"]
        ids = [e.get("PersonId") for e in entries]
        if not entries or any(not v for v in ids) or len(ids) != len(set(ids)):
            raise ValueError("Missing or repeated source player IDs")
        players[str(team.get("TeamId"))] = len(entries)
    return {
        "source_match_id": general.attrib["MatchId"],
        "home_team_id": general.get("HomeTeamId"),
        "away_team_id": general.get("GuestTeamId"),
        "pitch_length_m": length,
        "pitch_width_m": width,
        "registered_player_counts": players,
        # Deliberately do NOT claim starting lineup, 22 on-field or 25 Hz validated.
    }


def inspect_source_directory(
    directory: Path,
    *,
    metadata_sha256: str,
    events_sha256: str,
    verify_tracking: bool = False,
) -> dict[str, object]:
    """Fail closed for mismatched source IDs, digests and missing authorized files.

    metadata/events SHA-256 values must be obtained independently by the
    operator after an immutable-revision download. They verify local file
    stability but are NOT cryptographic proof of their upstream origin.
    Tracking's expected SHA is source-published and pinned in code.
    """
    if directory.name != MATCH_ID:
        raise ValueError("Expected exact IDSSE match directory J03WMX")
    paths = {kind: directory / name for kind, name in SOURCE_NAMES.items()}
    for kind in ("metadata", "events"):
        if not CHECKSUM.fullmatch(
            metadata_sha256 if kind == "metadata" else events_sha256
        ):
            raise ValueError(f"Valid operator {kind} SHA-256 required")
        if not paths[kind].is_file():
            raise ValueError(f"Required IDSSE local file missing: {SOURCE_NAMES[kind]}")
    metadata = _xml_from_verified_bytes(paths["metadata"], metadata_sha256)
    events = _xml_from_verified_bytes(paths["events"], events_sha256)
    details = _match_metadata(metadata)
    # Event payload grammar isn't yet independently audited against the
    # authentic upstream XML. Report ONLY well-formed XML, not event joins.
    event_elements = sum(_tag(e) == "Event" for e in events.iter())
    tracking_verified = False
    tracking_size: int | None = None
    if verify_tracking:
        if not paths["tracking"].is_file():
            raise ValueError("Real tracking file missing; cannot verify published digest")
        _, tracking_size = sha256_file(paths["tracking"], TRACKING_SHA256)
        tracking_verified = True

    return {
        "schema_version": 1,
        "provider": "idsse_sportec_open_data",
        "match_id": MATCH_ID,
        "upstream_revision": REVISION,
        "publisher": "Deutsche Fußball Liga (DFL)",
        "rights": "CC-BY-4.0_REQUIRES_DFL_AND_PUBLICATION_CREDIT",
        "source_files": {
            kind: {
                "url": source_url(kind),
                "sha256": (
                    TRACKING_SHA256 if kind == "tracking"
                    else metadata_sha256 if kind == "metadata" else events_sha256
                ),
                "verified_original_bytes": (
                    tracking_verified if kind == "tracking" else False
                ),
            }
            for kind in SOURCE_NAMES
        },
        "metadata": details,
        "events_xml_well_formed": True,
        "event_tag_count_unvalidated": event_elements,
        "tracking_sha256_verified": tracking_verified,
        "tracking_file_size_bytes": tracking_size,
        "tracking_frames_inspected": False,
        "source_sample_rate_verified": False,
        "player_ball_coverage_verified": False,
        "events_tracking_alignment_verified": False,
        "source_playback_ready": False,
        "public_replay_enabled": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--metadata-sha256", required=True)
    parser.add_argument("--events-sha256", required=True)
    parser.add_argument("--verify-tracking", action="store_true")
    args = parser.parse_args()
    report = inspect_source_directory(
        args.directory,
        metadata_sha256=args.metadata_sha256,
        events_sha256=args.events_sha256,
        verify_tracking=args.verify_tracking,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
