"""Source-observed, bounded Sportec FrameSet and shot-candidate audit.

No network, public API, frame interpolation, generated player positions or
presumed event-to-tracking synchronization. Authenticate original tracking
bytes before accepting a report as source-backed.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import isfinite
from pathlib import Path
from xml.etree import ElementTree as ET

from pitchvolt.idsse_source_audit import DFL_MATCH_ID, TRACKING_SHA256, sha256_file

_PERIODS = {"firstHalf": 1, "secondHalf": 2, "firstHalfExtra": 3, "secondHalfExtra": 4}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _safe_xml(path: Path):
    with path.open("rb") as source:
        preamble = source.read(8192).upper()
    if b"<!DOCTYPE" in preamble or b"<!ENTITY" in preamble:
        raise ValueError("Sportec XML cannot contain DTD or entity declarations")
    return ET.iterparse(path, events=("start", "end"))


def _point_values(attrs: dict[str, str], is_ball: bool) -> tuple[float, ...] | None:
    names = ("X", "Y", "Z") if is_ball else ("X", "Y")
    raw = [attrs.get(name) for name in names]
    if all(value is None or not value.strip() for value in raw):
        return None
    if any(value is None or not value.strip() for value in raw):
        raise ValueError("Partial Sportec position cannot be interpreted as measured")
    try:
        values = tuple(float(v) for v in raw)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid Sportec tracking coordinate") from exc
    if not all(isfinite(v) for v in values):
        raise ValueError("Non-finite Sportec tracking coordinate")
    if is_ball and values[2] < 0:
        raise ValueError("Ball height cannot be negative")
    return values


def inspect_frame_window(
    path: Path,
    *,
    period: int,
    first_frame: int,
    frame_count: int = 625,
    roster: dict[str, str] | None = None,
    require_original_digest: bool = True,
) -> dict[str, object]:
    """Scan per-object FrameSets with bounded memory and explicit coverage.

    Synthetic unit fixtures may set require_original_digest=False; the
    returned report then explicitly marks original bytes UNVERIFIED.
    """
    if period not in (1, 2, 3, 4) or first_frame < 0:
        raise ValueError("Valid source period and non-negative first_frame required")
    if not 2 <= frame_count <= 750:
        raise ValueError("Bounded original tracking window must contain 2..750 frames")
    if require_original_digest:
        sha256_file(path, TRACKING_SHA256)
    stop = first_frame + frame_count
    rows: dict[int, dict[str, object]] = defaultdict(
        lambda: {"players": {}, "ball": None, "time": None, "ball_possession": None}
    )
    current_period: int | None = None
    current_obj: str | None = None
    previous_by_obj: dict[str, int] = {}
    found_root = False
    ignored_objects: set[str] = set()
    root: ET.Element | None = None
    for action, element in _safe_xml(path):
        tag = _local(element.tag)
        if action == "start":
            if root is None:
                root = element
                if tag != "PutDataRequest":
                    raise ValueError("Unexpected Sportec tracking document root")
                found_root = True
            if tag == "FrameSet":
                if element.get("MatchId") != DFL_MATCH_ID:
                    raise ValueError("Sportec FrameSet belongs to another match")
                current_period = _PERIODS.get(element.get("GameSection", ""))
                current_obj = (
                    "ball" if element.get("TeamId") == "BALL"
                    else element.get("PersonId")
                )
                if current_period == period and not current_obj:
                    raise ValueError("FrameSet lacks registered object identity")
            elif tag == "Frame" and current_period == period and current_obj:
                attributes = element.attrib
                try:
                    fid = int(attributes["N"])
                except (KeyError, ValueError) as exc:
                    raise ValueError("Sportec Frame lacks numeric N") from exc
                if fid < first_frame or fid >= stop:
                    continue
                if current_obj != "ball" and roster is not None and current_obj not in roster:
                    ignored_objects.add(current_obj)
                    continue  # referees/officials, not fictional extra players
                prev = previous_by_obj.get(current_obj)
                if prev is not None and fid <= prev:
                    raise ValueError("Duplicate or unsorted tracking frame per object")
                previous_by_obj[current_obj] = fid
                try:
                    timestamp = datetime.fromisoformat(attributes["T"])
                except (KeyError, ValueError) as exc:
                    raise ValueError("Missing/invalid source frame timestamp") from exc
                if timestamp.utcoffset() is None:
                    raise ValueError("Tracking timestamp must include UTC offset")
                row = rows[fid]
                existing = row["time"]
                if existing is not None and abs((timestamp - existing).total_seconds()) > 0.002:
                    raise ValueError("Frame timestamp differs between source objects")
                row["time"] = timestamp
                coords = _point_values(attributes, is_ball=current_obj == "ball")
                if current_obj == "ball":
                    if row["ball"] is not None:
                        raise ValueError("Duplicate ball observation at source frame")
                    status = attributes.get("BallStatus")
                    if status not in ("0", "1"):
                        raise ValueError("BallStatus must be explicitly 0 or 1")
                    possession = attributes.get("BallPossession")
                    if possession not in (None, "0", "1", "2"):
                        raise ValueError("Unsupported source team possession flag")
                    row["ball"] = (coords, status)
                    row["ball_possession"] = possession
                else:
                    players = row["players"]
                    if current_obj in players:
                        raise ValueError("Duplicate player in the same source frame")
                    players[current_obj] = coords
        elif tag == "FrameSet":
            current_period = None
            current_obj = None
            # FrameSet is the complete processing unit; bounded XML memory.
            if root is not None:
                root.clear()
        elif tag == "Frame":
            element.clear()
    if not found_root:
        raise ValueError("Empty Sportec tracking source")
    ids = sorted(fid for fid in rows if rows[fid]["ball"] is not None)
    if len(ids) < 2:
        raise ValueError("Window has fewer than two source ball samples")
    stamps = [rows[fid]["time"] for fid in ids]
    regular = all(
        abs((stamps[i] - stamps[i - 1]).total_seconds() - (ids[i] - ids[i - 1]) / 25)
        <= 0.002
        for i in range(1, len(ids))
    )
    visible = [sum(coords is not None for coords in rows[fid]["players"].values()) for fid in ids]
    if any(n > 22 for n in visible):
        raise ValueError("More than 22 tracked players in a frame")
    if roster is not None:
        for fid in ids:
            sides: dict[str, int] = defaultdict(int)
            for player_id, coords in rows[fid]["players"].items():
                if coords is not None:
                    sides[roster[player_id]] += 1
            if any(v > 11 for v in sides.values()):
                raise ValueError("More than eleven tracked players on one team")
    ball_visible = sum(rows[fid]["ball"][0] is not None for fid in ids)
    return {
        "provider": "idsse_sportec",
        "source_match_id": DFL_MATCH_ID,
        "period": period,
        "requested_first_frame": first_frame,
        "requested_frame_count": frame_count,
        "observed_ball_frame_count": len(ids),
        "observed_ball_xyz_frame_count": ball_visible,
        "ball_xyz_missing_frame_count": len(ids) - ball_visible,
        "visible_player_count_min": min(visible),
        "visible_player_count_max": max(visible),
        "observed_complete_22_frame_count": sum(n == 22 for n in visible),
        "source_frame_timing_matches_nominal_25hz": regular,
        "ignored_unregistered_objects": len(ignored_objects),
        "source_tracking_sha256_verified": require_original_digest,
        "source_player_carrier_known": False,
        "event_frame_alignment_verified": False,
        "public_replay_enabled": False,
        "source_playback_ready": False,
    }


def shot_candidates(event_xml: Path) -> list[dict[str, object]]:
    """Return only shots with recorded CalculatedFrame; no timestamp guessing."""
    candidates: list[dict[str, object]] = []
    root: ET.Element | None = None
    for action, element in _safe_xml(event_xml):
        tag = _local(element.tag)
        if root is None and action == "start":
            root = element
            if tag != "PutDataRequest":
                raise ValueError("Unexpected Sportec event document root")
        if action != "end" or tag != "Event":
            continue
        if element.get("MatchId") != DFL_MATCH_ID:
            raise ValueError("Candidate shot event belongs to another match")
        shot = next((child for child in element.iter() if _local(child.tag) == "ShotAtGoal"), None)
        fid = element.get("CalculatedFrame")
        if shot is not None and fid is not None:
            try:
                number = int(fid)
                if number < 0:
                    raise ValueError()
                timestamp = datetime.fromisoformat(element.attrib["CalculatedTimestamp"])
                if timestamp.utcoffset() is None:
                    raise ValueError()
            except (ValueError, KeyError) as exc:
                raise ValueError("Malformed explicitly source-linked shot frame") from exc
            candidates.append({
                "source_event_id": element.get("EventId"),
                "calculated_frame": number,
                "source_timestamp": timestamp.isoformat(),
                "source_kind": "ShotAtGoal",
                "period": None,  # requires explicit source section reconciliation
            })
        element.clear()
        if root is not None:
            root.clear()
    return candidates
