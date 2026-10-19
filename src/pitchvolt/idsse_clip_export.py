"""Reproducible 25-second *observed* Sportec player/ball clip, offline only.

Reads SHA-pinned original match files. Never generates positional samples,
carries positions forward, infers ball carrier, or modifies public serving.
The compact JSON asset is a source-derived export subject to CC BY 4.0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from pitchvolt.idsse_frame_audit import (
    inspect_frame_window,
    registered_roster,
    shot_candidates,
)
from pitchvolt.idsse_source_audit import (
    DFL_MATCH_ID,
    MATCH_ID,
    REVISION,
    SOURCE_NAMES,
    TRACKING_SHA256,
    _xml_from_verified_bytes,
    inspect_source_directory,
    source_url,
)

EVENT_ID = "18226500000041"
EVENT_FRAME = 12519
FIRST_FRAME = 12219
SAMPLE_COUNT = 625
PERIOD = 1
RATE_HZ = 25
PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0
SCHEMA_VERSION = 1
ATTRIBUTION = (
    "Tracking and event data: Deutsche Fußball Liga (DFL); "
    "Bassek et al. (2025), An integrated dataset of spatiotemporal "
    "and event data in elite soccer, Scientific Data, "
    "https://doi.org/10.1038/s41597-025-04505-y; "
    "CC BY 4.0, https://creativecommons.org/licenses/by/4.0/; "
    "positions normalized by translation only; no TV footage."
)


def _teams(root: ET.Element) -> list[dict[str, str]]:
    general = next((x for x in root.iter() if x.tag.rsplit("}", 1)[-1] == "General"), None)
    if general is None or general.get("MatchId") != DFL_MATCH_ID:
        raise ValueError("Invalid source match identity")
    return [
        {
            "id": str(general.attrib[team_id]),
            "name": str(general.attrib[name]),
            "role": role,
        }
        for team_id, name, role in (
            ("HomeTeamId", "HomeTeamName", "home"),
            ("GuestTeamId", "GuestTeamName", "away"),
        )
    ]


def _pitch_position(raw: tuple[float, ...]) -> list[float]:
    """Sportec tracking uses pitch-center X/Y, not event coordinate origin."""
    return [raw[0] + PITCH_LENGTH_M / 2, raw[1] + PITCH_WIDTH_M / 2]


def _make_clip(
    original_rows: dict[int, dict[str, object]],
    *,
    roster: dict[str, str],
    teams: list[dict[str, str]],
    shot: dict[str, object],
    metadata_sha: str,
    events_sha: str,
) -> dict[str, Any]:
    if sorted(original_rows) != list(range(FIRST_FRAME, FIRST_FRAME + SAMPLE_COUNT)):
        raise ValueError("Original source window has missing or out-of-order frame IDs")
    if shot["source_event_id"] != EVENT_ID or shot["calculated_frame"] != EVENT_FRAME:
        raise ValueError("Expected original shot event/frame not present")
    source_time = datetime.fromisoformat(str(shot["source_timestamp"]))
    if source_time.utcoffset() is None:
        raise ValueError("Original shot timestamp missing timezone")

    team_ids = {team["id"] for team in teams}
    player_ids: set[str] = set()
    previous_time: datetime | None = None
    for frame_id in sorted(original_rows):
        frame = original_rows[frame_id]
        timestamp = frame["time"]
        if not isinstance(timestamp, datetime) or timestamp.utcoffset() is None:
            raise ValueError("Frame timestamp must be measured and timezone-aware")
        if previous_time is not None and abs(
            (timestamp - previous_time).total_seconds() - 1 / RATE_HZ
        ) > 0.002:
            raise ValueError("Source frame time is not continuous at 25 Hz")
        previous_time = timestamp
        players = frame["players"]
        if len(players) != 22 or any(coords is None for coords in players.values()):
            raise ValueError("Source clip must have exactly 22 observed players at each frame")
        sides = {team: 0 for team in team_ids}
        for player in players:
            team_id = roster.get(player)
            if team_id not in sides:
                raise ValueError("Observed player has no verified match-team identity")
            sides[team_id] += 1
            player_ids.add(player)
        if sorted(sides.values()) != [11, 11]:
            raise ValueError("Observed source frame lacks eleven players on each team")
        ball = frame["ball"]
        if ball is None or ball[0] is None or len(ball[0]) != 3:
            raise ValueError("Source clip requires independent observed ball XYZ")
        if frame["ball_possession"] not in (None, "0", "1", "2"):
            raise ValueError("Unsupported original ball team possession marker")
        if frame_id == EVENT_FRAME and abs(
            (timestamp - source_time).total_seconds()
        ) > 0.005:
            raise ValueError("Source shot event does not align to original ball frame")

    ordered_ids = sorted(player_ids)
    roster_entries = [
        {"source_player_id": player_id, "source_team_id": roster[player_id]}
        for player_id in ordered_ids
    ]
    source_frames: list[dict[str, Any]] = []
    for frame_id in sorted(original_rows):
        record = original_rows[frame_id]
        ball_xyz, state = record["ball"]
        # Exact source measurements, merely a known coordinate translation;
        # explicit nulls for unavailable participants, never forward fill.
        source_frames.append({
            "source_frame": frame_id,
            "timestamp": record["time"].isoformat(timespec="milliseconds"),
            "players_xy_m": [
                _pitch_position(record["players"][player])
                if player in record["players"] else None
                for player in ordered_ids
            ],
            "ball_xyz_m": [*_pitch_position(ball_xyz), ball_xyz[2]],
            "source_ball_status": state,
            "source_ball_possession_code": record["ball_possession"],
        })

    return {
        "asset_kind": "source_observed_sportec_clip",
        "schema_version": SCHEMA_VERSION,
        "source": {
            "dataset": "IDSSE / Sportec Open Data",
            "publisher": "Deutsche Fußball Liga (DFL)",
            "license": "CC-BY-4.0",
            "attribution": ATTRIBUTION,
            "revision": REVISION,
            "original_tracking_sha256": TRACKING_SHA256,
            "metadata_sha256": metadata_sha,
            "events_sha256": events_sha,
            "original_urls": {kind: source_url(kind) for kind in SOURCE_NAMES},
            "derived_from_source_coordinates": True,
        },
        "match": {
            "id": DFL_MATCH_ID,
            "dataset_match_id": MATCH_ID,
            "teams": teams,
            "period": PERIOD,
        },
        "segment": {
            "source_event_id": EVENT_ID,
            "source_event_kind": "ShotAtGoal",
            "source_shot_frame": EVENT_FRAME,
            "source_shot_timestamp": source_time.isoformat(timespec="milliseconds"),
            "first_frame": FIRST_FRAME,
            "last_frame": FIRST_FRAME + SAMPLE_COUNT - 1,
            "sample_count": SAMPLE_COUNT,
            "frame_rate_hz": RATE_HZ,
            "duration_seconds": SAMPLE_COUNT / RATE_HZ,
        },
        "coordinates": {
            "pitch_length_m": PITCH_LENGTH_M,
            "pitch_width_m": PITCH_WIDTH_M,
            "source_origin": "pitch_center",
            "output_origin": "pitch_minimum_corner",
            "transformation": "x=raw_x+52.5,y=raw_y+34,z=raw_z",
            "ball_z_units": "meters",
            "no_interpolation": True,
        },
        "roster": roster_entries,
        "frames": source_frames,
        "player_ball_coverage_verified": True,
        "player_carrier_known": False,
        "public_replay_enabled": False,
    }


def export_verified_clip(
    directory: Path,
    *,
    metadata_sha256: str,
    events_sha256: str,
    destination: Path,
) -> dict[str, object]:
    """Full source digest + event/frame evidence; atomic deterministic JSON."""
    if directory.name != MATCH_ID:
        raise ValueError("Expected immutable source match J03WMX")
    if destination.exists():
        raise ValueError("Refusing to overwrite existing observed replay asset")
    # Verify real tracking SHA and both local input checks BEFORE extracting.
    verified = inspect_source_directory(
        directory,
        metadata_sha256=metadata_sha256,
        events_sha256=events_sha256,
        verify_tracking=True,
    )
    if not verified["tracking_sha256_verified"] or not verified["metadata"]["pitch_length_m"] == 105:
        raise ValueError("Authentic source verification incomplete")
    original_meta = _xml_from_verified_bytes(
        directory / SOURCE_NAMES["metadata"], metadata_sha256
    )
    roster = registered_roster(original_meta)
    teams = _teams(original_meta)
    candidates = shot_candidates(directory / SOURCE_NAMES["events"])
    source_shots = [x for x in candidates if x["source_event_id"] == EVENT_ID]
    if len(source_shots) != 1:
        raise ValueError("Source clip shot not uniquely identified")
    shot = source_shots[0]
    if shot["calculated_frame"] != EVENT_FRAME:
        raise ValueError("Source shot's original frame has changed")

    rows: dict[int, dict[str, object]] = {}
    report = inspect_frame_window(
        directory / SOURCE_NAMES["tracking"],
        period=PERIOD,
        first_frame=FIRST_FRAME,
        frame_count=SAMPLE_COUNT,
        roster=roster,
        require_original_digest=True,
        anchor_frame=EVENT_FRAME,
        anchor_timestamp=str(shot["source_timestamp"]),
        _rows_out=rows,
    )
    if not (
        report["source_tracking_sha256_verified"]
        and report["event_frame_alignment_verified"]
        and report["source_frame_timing_matches_nominal_25hz"]
        and report["observed_ball_xyz_frame_count"] == SAMPLE_COUNT
        and report["observed_complete_22_frame_count"] == SAMPLE_COUNT
    ):
        raise ValueError("Original clip fails complete ball/22-player/event coverage")

    payload = _make_clip(
        rows, roster=roster, teams=teams, shot=shot,
        metadata_sha=metadata_sha256, events_sha=events_sha256,
    )
    result = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    result_bytes = (result + "\n").encode("utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(result_bytes)
    return {
        "asset_kind": "source_observed_sportec_clip",
        "schema_version": SCHEMA_VERSION,
        "match_id": DFL_MATCH_ID,
        "source_event_id": EVENT_ID,
        "source_shot_frame": EVENT_FRAME,
        "frame_count": SAMPLE_COUNT,
        "players_per_frame": 22,
        "measured_ball_xyz_frames": SAMPLE_COUNT,
        "asset_size_bytes": len(result_bytes),
        "asset_sha256": hashlib.sha256(result_bytes).hexdigest(),
        "original_tracking_sha256_verified": True,
        "source_event_aligned": True,
        "attribution": ATTRIBUTION,
        "no_inferred_player_carrier": True,
        "public_replay_enabled": False,
    }


def verify_compact_asset(path: Path, *, expected_sha256: str | None = None) -> dict[str, object]:
    """Independently validate compact file structure, exact timebase and roster.

    This cannot independently prove source coordinates: that comes from the
    pinned-source producer's full original-byte verification above.
    """
    original = path.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("Compact observed asset SHA-256 mismatch")
    if len(original) > 10 * 1024 * 1024:
        raise ValueError("Unexpectedly large derived sample")
    obj = json.loads(original)
    if obj.get("asset_kind") != "source_observed_sportec_clip":
        raise ValueError("Not an observed Sportec source clip")
    if obj.get("schema_version") != 1:
        raise ValueError("Unsupported observed clip schema")
    if obj.get("source", {}).get("original_tracking_sha256") != TRACKING_SHA256:
        raise ValueError("Original source SHA missing or changed")
    if obj.get("public_replay_enabled") is not False:
        raise ValueError("Observed clip cannot enable serving in v1")
    if obj.get("player_carrier_known") is not False:
        raise ValueError("Observed sample cannot invent a source carrier")
    if obj.get("match", {}).get("id") != DFL_MATCH_ID:
        raise ValueError("Observed clip match identity mismatch")
    segment = obj.get("segment", {})
    if (segment.get("first_frame"), segment.get("last_frame")) != (
        FIRST_FRAME, FIRST_FRAME + SAMPLE_COUNT - 1
    ):
        raise ValueError("Observed segment frame range mismatch")
    if segment.get("source_shot_frame") != EVENT_FRAME:
        raise ValueError("Observed source shot frame mismatch")
    if segment.get("source_event_id") != EVENT_ID:
        raise ValueError("Observed source shot event mismatch")
    if segment.get("frame_rate_hz") != RATE_HZ:
        raise ValueError("Observed frame rate mismatch")
    roster = obj.get("roster", [])
    ids = [p.get("source_player_id") for p in roster]
    teams = {t["id"] for t in obj["match"]["teams"]}
    if len(ids) != len(set(ids)) or any(not p or p["source_team_id"] not in teams for p in roster):
        raise ValueError("Invalid or duplicate observed source roster")
    frames = obj.get("frames", [])
    if len(frames) != SAMPLE_COUNT:
        raise ValueError("Incomplete compact original sequence")
    prev_time: datetime | None = None
    event_time = datetime.fromisoformat(segment["source_shot_timestamp"])
    if event_time.utcoffset() is None:
        raise ValueError("Source event timestamp lacks timezone")
    for index, row in enumerate(frames):
        if row["source_frame"] != FIRST_FRAME + index:
            raise ValueError("Source frame ID missing or out of order")
        timestamp = datetime.fromisoformat(row["timestamp"])
        if timestamp.utcoffset() is None:
            raise ValueError("Source frame timestamp lacks timezone")
        if prev_time is not None and abs(
            (timestamp - prev_time).total_seconds() - 1 / RATE_HZ
        ) > 0.002:
            raise ValueError("Source tracking sample time gap")
        prev_time = timestamp
        samples = row["players_xy_m"]
        if len(samples) != len(roster):
            raise ValueError("Source roster size differs from observed samples")
        observed_teams: dict[str, int] = {team: 0 for team in teams}
        for player, coords in zip(roster, samples, strict=True):
            if coords is None:
                continue
            if len(coords) != 2 or not all(isinstance(n, (int, float)) and
                                              not isinstance(n, bool) and
                                              abs(n) < 10000 for n in coords):
                raise ValueError("Invalid observed player coordinates")
            observed_teams[player["source_team_id"]] += 1
        if sorted(observed_teams.values()) != [11, 11]:
            raise ValueError("Compact frame lacks 11 observed players per team")
        ball = row["ball_xyz_m"]
        if ball is None or len(ball) != 3 or not all(
            isinstance(n, (int, float)) and not isinstance(n, bool)
            and abs(n) < 10000 for n in ball
        ) or ball[2] < 0:
            raise ValueError("Original observed ball XYZ missing or invalid")
        if row["source_frame"] == EVENT_FRAME and abs(
            (timestamp - event_time).total_seconds()
        ) > 0.005:
            raise ValueError("Source event not aligned to observed ball frame")
    return {
        "asset_sha256": digest,
        "schema_version": 1,
        "frame_count": SAMPLE_COUNT,
        "players_per_frame": 22,
        "ball_xyz_frames": SAMPLE_COUNT,
        "original_source_sha256": TRACKING_SHA256,
        "exact_shot_aligned": True,
        "public_replay_enabled": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--metadata-sha256", required=True)
    parser.add_argument("--events-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(export_verified_clip(
        args.directory,
        metadata_sha256=args.metadata_sha256,
        events_sha256=args.events_sha256,
        destination=args.output,
    ), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
