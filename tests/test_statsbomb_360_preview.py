"""Visual snapshot is solely source-derived and safe for local inspection."""
from dataclasses import replace
from pathlib import Path

import pytest

from pitchvolt.events import Point
from pitchvolt.providers.statsbomb_360 import (
    Historical360Frame,
    Observed360Player,
)
from pitchvolt.providers.statsbomb_360_replay import HistoricalReplayMoment
from pitchvolt.statsbomb_360_preview import (
    render_full_xi_gallery_html,
    render_historical_frame_html,
)


def moment(*, on_pitch=2, off_pitch=1):
    players = tuple(
        Observed360Player(
            observation_index=i,
            source_location=(float(10 + i), 34.0),
            position=Point(x=10 + i, y=34) if i < on_pitch else None,
            teammate=i % 2 == 0, actor=i == 0, keeper=False,
            player_id=9 if i == 0 else None,
        )
        for i in range(on_pitch + off_pitch)
    )
    frame = Historical360Frame(
        event_id="source-uuid", period=1, clock_ms=1200, event_team_id=20,
        visible_area=(0, 0, 120, 0, 120, 80), observations=players,
    )
    return HistoricalReplayMoment(
        match_id="fixture-123", event_id="source-uuid", clock_ms=1200, period=1,
        event_sha256="a" * 64, frame_sha256="b" * 64, frame=frame,
    )


def test_only_genuine_on_pitch_detections_are_rendered():
    html = render_historical_frame_html(moment())
    assert "3 observed, 2 on-field renderable" in html
    assert "Source player 9" in html
    assert "Anonymous detection" in html
    assert 'cx="10" cy="34"' in html
    assert 'cx="11" cy="34"' in html
    assert 'cx="12" cy="34"' not in html
    assert "No positions have been inferred or interpolated" in html
    assert "Events SHA-256: <code>" + "a" * 64 in html


def test_no_source_frame_contains_no_actor_or_players():
    missing = replace(moment(), frame=None)
    html = render_historical_frame_html(missing)
    assert "No 360 frame for this source event" in html
    assert "0 observed, 0 on-field renderable" in html
    assert "Source player 9" not in html
    assert "<title>Anonymous detection</title>" not in html


def test_exact_full_xi_is_not_claimed_for_any_partial_frame():
    scene = moment(on_pitch=2, off_pitch=0)
    assert not scene.full_xi
    assert "Partial observed frame" in render_historical_frame_html(scene)


def test_user_controlled_event_identifier_is_html_escaped():
    scene = replace(moment(), event_id="<img src=x onerror=alert(1)>")
    html = render_historical_frame_html(scene)
    assert "<img src=x onerror=alert(1)>" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html


def test_missing_local_bundle_cannot_generate_a_preview(tmp_path: Path):
    from pitchvolt.statsbomb_360_preview import create_local_preview

    out = tmp_path / "frame.html"
    with pytest.raises(FileNotFoundError):
        create_local_preview(
            tmp_path, match_id="123", event_id="source-uuid",
            lineup_sha256="a" * 64, frame_sha256="b" * 64,
            output=out,
        )
    assert not out.exists()


def test_full_xi_gallery_shows_only_exact_source_complete_frames():
    complete = moment(on_pitch=22, off_pitch=0)
    partial = replace(moment(on_pitch=2, off_pitch=0), event_id="not-complete")
    html = render_full_xi_gallery_html([partial, complete])
    assert "1 genuine 11v11 source-event frames" in html
    assert "not-complete" not in html
    assert "source-uuid" in html
    assert "22 observed" in html
    assert "No interpolated or illustrative player positions" in html
    assert html.count("<iframe ") == 1
    assert "Source player 9" in html
    assert "Anonymous detection" in html
    assert 'sandbox=""' in html


def test_full_xi_gallery_handles_zero_source_complete_frames():
    html = render_full_xi_gallery_html([moment(on_pitch=2, off_pitch=0)])
    assert "No complete 11v11 freeze frames" in html
    assert "<iframe" not in html


def test_full_xi_gallery_rejects_cross_match_or_hash_mixing():
    good = moment(on_pitch=22, off_pitch=0)
    wrong_match = replace(good, match_id="other-source-match")
    wrong_hash = replace(good, frame_sha256="c" * 64)
    with pytest.raises(ValueError, match="cannot mix"):
        render_full_xi_gallery_html([good, wrong_match])
    with pytest.raises(ValueError, match="cannot mix"):
        render_full_xi_gallery_html([good, wrong_hash])


def test_full_xi_gallery_requires_verified_local_files(tmp_path: Path):
    from pitchvolt.statsbomb_360_preview import create_full_xi_gallery

    out = tmp_path / "full-xi.html"
    with pytest.raises(FileNotFoundError):
        create_full_xi_gallery(
            tmp_path, match_id="123",
            lineup_sha256="a" * 64, frame_sha256="b" * 64,
            output=out,
        )
    assert not out.exists()
