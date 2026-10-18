"""Offline SVG/HTML inspection of original, hash-verified StatsBomb 360 frames.

Generate a *local* preview of one source event. No server, CDN, external
assets, remote inference, synthetic overlays or persistent tracking assumptions.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from html import escape
from pathlib import Path

from pitchvolt.providers.statsbomb_360 import Historical360Bundle, load_historical_360
from pitchvolt.providers.statsbomb_360_replay import (
    HistoricalReplayMoment,
    historical_moment_at_event,
)
from pitchvolt.providers.statsbomb_historical import HistoricalFixture
from pitchvolt.statsbomb_bundle_report import load_verified_historical_bundle

_PITCH = """<rect x="0" y="0" width="105" height="68" fill="#214a2a"/>
<rect x="0.7" y="0.7" width="103.6" height="66.6" fill="none" stroke="white" stroke-width=".2"/>
<line x1="52.5" y1=".7" x2="52.5" y2="67.3" stroke="white" stroke-width=".2"/>
<circle cx="52.5" cy="34" r="9.15" fill="none" stroke="white" stroke-width=".2"/>
<rect x=".7" y="13.84" width="16.5" height="40.32" fill="none" stroke="white" stroke-width=".2"/>
<rect x="87.8" y="13.84" width="16.5" height="40.32" fill="none" stroke="white" stroke-width=".2"/>
<rect x=".7" y="24.84" width="5.5" height="18.32" fill="none" stroke="white" stroke-width=".2"/>
<rect x="98.8" y="24.84" width="5.5" height="18.32" fill="none" stroke="white" stroke-width=".2"/>"""


def render_historical_frame_html(moment: HistoricalReplayMoment) -> str:
    """Render actual on-field objects only; off-field records remain in counts."""
    observed = moment.observed
    inside = moment.renderable
    teammate = sum(p.teammate for p in observed)
    opponent = len(observed) - teammate
    content: list[str] = []
    for player in inside:
        point = player.position
        assert point is not None  # filtered via moment.renderable
        color = "#6ed0ff" if player.teammate else "#ffb56b"
        identity = f"Source player {player.player_id}" if player.player_id else "Anonymous detection"
        title = escape(
            f"{identity}; {'event team' if player.teammate else 'opponent'};"
            f" {'actor' if player.actor else 'non-actor'}; frame slot {player.observation_index}"
        )
        if player.actor:
            content.append(
                f'<circle cx="{point.x:g}" cy="{point.y:g}" r="1.9" '
                'fill="none" stroke="#d8ff5c" stroke-width=".45"/>'
            )
        content.append(
            f'<circle cx="{point.x:g}" cy="{point.y:g}" r="1.15" '
            f'fill="{color}" stroke="#102318" stroke-width=".2">'
            f"<title>{title}</title></circle>"
        )
    label = "Complete observed 11v11 frame" if moment.full_xi else "Partial observed frame"
    if moment.frame is None:
        label = "No 360 frame for this source event"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Source-backed 360 frame · {escape(moment.event_id)}</title>
<style>
body {{font:16px system-ui;background:#0b2016;color:#e6f8ea;max-width:1100px;margin:auto;padding:24px}}
svg {{display:block;width:100%;height:auto;max-width:1050px;border:1px solid #668876}}
aside {{line-height:1.7;color:#b7cfbd}}
code {{overflow-wrap:anywhere}}
</style>
</head><body>
<h1>Verified historical event snapshot</h1>
<p>{escape(label)} · {len(observed)} observed, {len(inside)} on-field renderable</p>
<svg viewBox="0 0 105 68" role="img" aria-label="Observed positions from exact source event">
{_PITCH}
{''.join(content)}
</svg>
<aside>
<p>Event-team detections: {teammate} · opponent detections: {opponent}.
Blue: event team; amber: opponent; green ring: recorded actor. Other players
have no persistent identities. The source is a freeze frame, not player tracking.</p>
<p>Match <code>{escape(moment.match_id)}</code> · event
<code>{escape(moment.event_id)}</code> · period {moment.period} ·
source clock {moment.clock_ms} ms.</p>
<p>Events SHA-256: <code>{escape(moment.event_sha256)}</code><br>
360 SHA-256: <code>{escape(moment.frame_sha256)}</code></p>
<p>Source: StatsBomb Open Data (Hudl).
Original observations may include off-field positions intentionally excluded
from pitch drawing. No positions have been inferred or interpolated.</p>
</aside></body></html>"""



def render_full_xi_gallery_html(moments: Iterable[HistoricalReplayMoment]) -> str:
    """Render a local gallery of *only* original complete 11v11 freeze frames.

    A frame may include off-pitch observations that are not drawn. Each entry
    remains an event-exact snapshot; no actors are carried between snapshots.
    """
    complete = tuple(moment for moment in moments if moment.full_xi)
    if complete and any(
        (moment.match_id, moment.event_sha256, moment.frame_sha256)
        != (complete[0].match_id, complete[0].event_sha256, complete[0].frame_sha256)
        for moment in complete
    ):
        raise ValueError("Full-XI gallery cannot mix matches or source fingerprints")

    cards: list[str] = []
    for index, moment in enumerate(complete):
        # The existing single-frame renderer is authoritative: no second
        # implementation of field transforms, identities, or drawing rules.
        embedded = escape(render_historical_frame_html(moment), quote=True)
        title = escape(f"Event {moment.event_id} · period {moment.period} · {moment.clock_ms} ms")
        cards.append(
            f'<details{" open" if index == 0 else ""}>'
            f"<summary>{title} · 22 observed</summary>"
            f'<iframe title="{title}" loading="lazy" sandbox="" '
            f'srcdoc="{embedded}"></iframe></details>'
        )
    message = (
        f"{len(complete)} genuine 11v11 source-event frames. "
        "Each shows only in-bounds recorded positions."
        if complete
        else "No complete 11v11 freeze frames in these verified source files."
    )
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verified 360 full-XI source frame gallery</title>
<style>
body {{font:16px system-ui;background:#0b2016;color:#e6f8ea;max-width:1150px;margin:auto;padding:24px}}
details {{margin:16px 0;border:1px solid #668876;padding:12px}}
summary {{cursor:pointer;color:#b6e64b;overflow-wrap:anywhere}}
iframe {{border:0;width:100%;min-height:850px;background:#0b2016}}
p {{color:#b7cfbd;line-height:1.6}}
</style></head><body>
<h1>Verified complete 11v11 source frames</h1>
<p>{message}</p>
<p>StatsBomb Open Data (Hudl). These are independent, event-exact camera
freeze frames, not continuous player tracking. Non-actors are anonymous.
Off-pitch coordinates are preserved in counts but never moved onto the field.
No interpolated or illustrative player positions are displayed.</p>
{''.join(cards)}
</body></html>"""


def _verified_sources(
    directory: Path, *, match_id: str, lineup_sha256: str, frame_sha256: str,
) -> tuple[HistoricalFixture, Historical360Bundle]:
    historical = load_verified_historical_bundle(
        directory, match_id=match_id, lineup_sha256=lineup_sha256
    )
    bundle = load_historical_360(
        directory / f"{match_id}.360.json",
        historical.fixture, expected_sha256=frame_sha256,
    )
    return historical.fixture, bundle


def create_full_xi_gallery(
    directory: Path, *, match_id: str, lineup_sha256: str,
    frame_sha256: str, output: Path,
) -> None:
    """Never publish original data: write only to a new local HTML file."""
    if output.exists():
        raise FileExistsError("Gallery output already exists")
    fixture, bundle = _verified_sources(
        directory, match_id=match_id, lineup_sha256=lineup_sha256,
        frame_sha256=frame_sha256,
    )
    moments = (
        historical_moment_at_event(fixture, bundle, frame.event_id)
        for frame in bundle.frames
        if frame.has_observed_full_xi
    )
    output.write_text(render_full_xi_gallery_html(moments), encoding="utf-8")

def create_local_preview(
    directory: Path, *, match_id: str, event_id: str,
    lineup_sha256: str, frame_sha256: str, output: Path,
) -> None:
    """Refuse overwrite and require original digest-verified source files."""
    if output.exists():
        raise FileExistsError("Preview output already exists")
    fixture, bundle = _verified_sources(
        directory, match_id=match_id, lineup_sha256=lineup_sha256,
        frame_sha256=frame_sha256,
    )
    moment = historical_moment_at_event(fixture, bundle, event_id)
    output.write_text(render_historical_frame_html(moment), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--match-id", required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--event-id")
    selection.add_argument("--full-xi-gallery", action="store_true")
    parser.add_argument("--lineup-sha256", required=True)
    parser.add_argument("--frame-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.full_xi_gallery:
        create_full_xi_gallery(
            args.directory, match_id=args.match_id,
            lineup_sha256=args.lineup_sha256, frame_sha256=args.frame_sha256,
            output=args.output,
        )
    else:
        assert args.event_id is not None
        create_local_preview(
            args.directory, match_id=args.match_id, event_id=args.event_id,
            lineup_sha256=args.lineup_sha256, frame_sha256=args.frame_sha256,
            output=args.output,
        )
    print(f"Verified local preview: {args.output}")


if __name__ == "__main__":
    main()
