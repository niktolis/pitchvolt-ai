"""Sportec-shaped original synthetic XML tests; no copied DFL match data."""
import pytest

from pitchvolt.idsse_frame_audit import inspect_frame_window, shot_candidates

MATCH = "DFL-MAT-J03WMX"
BALL = 'TeamId="BALL" PersonId="DFL-OBJ-000BALL"'


def _source(tmp_path, *, no_ball=False, missing_ball=False, duplicate=False,
            wrong_match=False, bad_time=False, bad_player=False, other_objects=False):
    ids = [10000, 10001, 10002]

    def block(identity, player=False):
        frames = []
        for n in ids:
            sec = (n - 10000) * 0.04
            t = f"2023-05-27T15:30:{sec:06.3f}+02:00"
            if bad_time and player:
                t = "2023-05-27T15:30:01.000+02:00"
            pos = (
                "" if missing_ball and not player else
                'X="2.69" Y="0.26" Z="0.06"' if not player else
                'X="-1.5" Y="2.5"'
            )
            suffix = 'BallStatus="1" BallPossession="2"' if not player else ""
            frames.append(f'<Frame N="{n}" T="{t}" {pos} {suffix} />')
        if duplicate:
            frames.append(frames[-1])
        which = "DFL-MAT-NOTTHIS" if wrong_match else MATCH
        return (
            f'<FrameSet GameSection="firstHalf" MatchId="{which}" {identity}>'
            + "".join(frames) + "</FrameSet>"
        )

    chunks = [] if no_ball else [block(BALL)]
    chunks.append(block('PersonId="DFL-OBJ-1" TeamId="H"', player=True))
    if other_objects:
        chunks.append(block('PersonId="REF-ID" TeamId="REF"', player=True))
    if bad_player:
        chunks.append(block('PersonId="DFL-OBJ-1" TeamId="H"', player=True))
    f = tmp_path / "synthetic.xml"
    f.write_text("<PutDataRequest><Positions>" + "".join(chunks) + "</Positions></PutDataRequest>")
    return f


def _run(path):
    return inspect_frame_window(
        path, period=1, first_frame=10000, frame_count=3,
        roster={"DFL-OBJ-1": "home"}, require_original_digest=False,
    )


def test_synthetic_coverage_never_misrepresented_as_authorized_source(tmp_path):
    report = _run(_source(tmp_path))
    assert report["observed_ball_frame_count"] == 3
    assert report["observed_ball_xyz_frame_count"] == 3
    assert report["visible_player_count_min"] == report["visible_player_count_max"] == 1
    assert report["observed_complete_22_frame_count"] == 0
    assert report["source_frame_timing_matches_nominal_25hz"]
    assert not report["source_tracking_sha256_verified"]
    assert not report["source_player_carrier_known"]
    assert not report["event_frame_alignment_verified"]
    assert not report["public_replay_enabled"]
    assert not report["source_playback_ready"]


def test_default_requires_actual_official_source_digest(tmp_path):
    path = _source(tmp_path)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        inspect_frame_window(path, period=1, first_frame=10000, frame_count=3)


def test_missing_ball_xyz_stays_explicitly_missing(tmp_path):
    report = _run(_source(tmp_path, missing_ball=True))
    assert report["observed_ball_frame_count"] == 3
    assert report["observed_ball_xyz_frame_count"] == 0
    assert report["ball_xyz_missing_frame_count"] == 3


@pytest.mark.parametrize(("change", "message"), [
    ({"no_ball": True}, "fewer than two source ball samples"),
    ({"duplicate": True}, "Duplicate or unsorted"),
    ({"wrong_match": True}, "another match"),
    ({"bad_time": True}, "timestamp differs"),
    ({"bad_player": True}, "Duplicate or unsorted"),
])
def test_invalid_source_data_rejected_without_fallback(tmp_path, change, message):
    with pytest.raises(ValueError, match=message):
        _run(_source(tmp_path, **change))


def test_referee_positions_are_not_counted_as_extra_players(tmp_path):
    report = _run(_source(tmp_path, other_objects=True))
    assert report["visible_player_count_max"] == 1
    assert report["ignored_unregistered_objects"] == 1


def test_window_requires_bounded_request(tmp_path):
    file = _source(tmp_path)
    for invalid in [
        {"period": 5, "first_frame": 10000, "frame_count": 3},
        {"period": 1, "first_frame": 10000, "frame_count": 1000},
        {"period": 1, "first_frame": -1, "frame_count": 3},
    ]:
        with pytest.raises(ValueError):
            inspect_frame_window(file, require_original_digest=False, **invalid)


def test_shot_candidates_never_invent_frame_or_period(tmp_path):
    path = tmp_path / "events.xml"
    path.write_text(
        '<PutDataRequest><Event MatchId="DFL-MAT-J03WMX" EventId="shot-1" '
        'CalculatedFrame="12000" CalculatedTimestamp="2023-05-27T15:30:02+02:00">'
        '<ShotAtGoal/></Event><Event MatchId="DFL-MAT-J03WMX" EventId="pass-1">'
        '<Play/></Event><Event MatchId="DFL-MAT-J03WMX" EventId="shot-2">'
        '<ShotAtGoal/></Event></PutDataRequest>'
    )
    assert shot_candidates(path) == [{
        "source_event_id": "shot-1",
        "calculated_frame": 12000,
        "source_timestamp": "2023-05-27T15:30:02+02:00",
        "source_kind": "ShotAtGoal",
        "period": None,
    }]


def test_cross_match_or_xml_entity_attack_rejected(tmp_path):
    path = tmp_path / "events.xml"
    path.write_text('<PutDataRequest><Event MatchId="OTHER"/></PutDataRequest>')
    with pytest.raises(ValueError, match="another match"):
        shot_candidates(path)
    path.write_text(
        '<!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
        '<PutDataRequest/>'
    )
    with pytest.raises(ValueError, match="DTD or entity"):
        shot_candidates(path)


def test_metadata_roster_authority_and_duplicate_rejection():
    from xml.etree import ElementTree as ET
    from pitchvolt.idsse_frame_audit import registered_roster

    root = ET.fromstring(
        '<PutDataRequest><Teams>'
        '<Team TeamId="home"><Players><Player PersonId="one"/></Players></Team>'
        '<Team TeamId="away"><Players><Player PersonId="two"/></Players></Team>'
        '</Teams></PutDataRequest>'
    )
    assert registered_roster(root) == {"one": "home", "two": "away"}
    root.find(".//Team[@TeamId='away']/Players/Player").set("PersonId", "one")
    with pytest.raises(ValueError, match="duplicate registered source player"):
        registered_roster(root)
