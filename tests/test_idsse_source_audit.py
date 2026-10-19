"""IDSSE source audit: original tiny synthetic XML, never copied DFL match bytes."""
import hashlib

import pytest

from pitchvolt.idsse_source_audit import (
    MATCH_ID,
    REVISION,
    SOURCE_NAMES,
    TRACKING_SHA256,
    inspect_source_directory,
    sha256_file,
    source_url,
)


def _file(folder, name, content):
    path = folder / name
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def _input(tmp_path, *, wrong_match=False, malformed_event=False, pitch="105"):
    directory = tmp_path / MATCH_ID
    directory.mkdir()
    match = "DFL-MAT-J03WQQ" if wrong_match else "DFL-MAT-J03WMX"
    metadata = (
        '<PutDataRequest><MatchInformation>'
        f'<General MatchId="{match}" HomeTeamName="1. FC Köln" '
        'GuestTeamName="FC Bayern München" HomeTeamId="DFL-CLU-HOME" '
        'GuestTeamId="DFL-CLU-AWAY" />'
        f'<Environment PitchX="{pitch}" PitchY="68" />'
        '<Teams><Team TeamId="DFL-CLU-HOME"><Players>'
        '<Player PersonId="DFL-OBJ-1"/><Player PersonId="DFL-OBJ-2"/>'
        '</Players></Team>'
        '<Team TeamId="DFL-CLU-AWAY"><Players>'
        '<Player PersonId="DFL-OBJ-3"/><Player PersonId="DFL-OBJ-4"/>'
        '</Players></Team></Teams></MatchInformation></PutDataRequest>'
    ).encode()
    events = (
        b"<PutDataRequest><Events><Event ID='e1' />"
        b"<Event ID='e2' /></Events></PutDataRequest>"
        if not malformed_event else b"<PutDataRequest><Events>"
    )
    hashes = {
        "metadata": _file(directory, SOURCE_NAMES["metadata"], metadata),
        "events": _file(directory, SOURCE_NAMES["events"], events),
    }
    return directory, hashes


def _audit(directory, hashes, **overrides):
    return inspect_source_directory(
        directory,
        metadata_sha256=overrides.pop("metadata_sha256", hashes["metadata"]),
        events_sha256=overrides.pop("events_sha256", hashes["events"]),
        **overrides,
    )


def test_selected_official_revision_and_three_source_urls_are_immutable():
    assert len(REVISION) == 40
    for kind in SOURCE_NAMES:
        url = source_url(kind)
        assert REVISION in url
        assert "resolve/main/" not in url
        assert url.endswith(SOURCE_NAMES[kind])
    assert TRACKING_SHA256 == (
        "d3dd92e509421a6466acb0a083c009035f1751bc5fd9ef42ffa8f20d01cf7d49"
    )


def test_metadata_and_event_preflight_reports_truthfully_unverified_tracking(tmp_path):
    directory, digests = _input(tmp_path)
    report = _audit(directory, digests)
    assert report["match_id"] == MATCH_ID
    assert report["metadata"]["source_match_id"] == "DFL-MAT-J03WMX"
    assert report["metadata"]["pitch_length_m"] == 105
    assert report["metadata"]["pitch_width_m"] == 68
    assert report["metadata"]["registered_player_counts"] == {
        "DFL-CLU-HOME": 2, "DFL-CLU-AWAY": 2,
    }
    assert report["events_xml_well_formed"]
    assert report["event_tag_count_unvalidated"] == 2
    assert not report["tracking_sha256_verified"]
    assert not report["tracking_frames_inspected"]
    assert not report["player_ball_coverage_verified"]
    assert not report["events_tracking_alignment_verified"]
    assert not report["source_playback_ready"]
    assert not report["public_replay_enabled"]
    assert report["rights"] == "CC-BY-4.0_REQUIRES_DFL_AND_PUBLICATION_CREDIT"
    assert not report["source_files"]["events"]["verified_original_bytes"]
    assert report["source_files"]["tracking"]["sha256"] == TRACKING_SHA256
    assert "x_coordinate" not in str(report)


def test_tracking_mode_fails_closed_if_original_file_is_absent_or_unverified(tmp_path):
    directory, digests = _input(tmp_path)
    with pytest.raises(ValueError, match="Real tracking file missing"):
        _audit(directory, digests, verify_tracking=True)
    fake = directory / SOURCE_NAMES["tracking"]
    fake.write_bytes(b"not a real Sportec XML file")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _audit(directory, digests, verify_tracking=True)


def test_operator_provided_digest_is_validated_but_not_proof_of_origin(tmp_path):
    directory, digests = _input(tmp_path)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _audit(directory, digests, metadata_sha256="0" * 64)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        _audit(directory, digests, events_sha256="0" * 64)
    with pytest.raises(ValueError, match="Valid operator events SHA-256 required"):
        _audit(directory, digests, events_sha256="BAD")


def test_wrong_match_metadata_and_pitch_are_rejected(tmp_path):
    directory, hashes = _input(tmp_path, wrong_match=True)
    with pytest.raises(ValueError, match="cross-match"):
        _audit(directory, hashes)
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(ValueError, match="exact IDSSE match directory"):
        _audit(other, hashes)


def test_malformed_or_inappropriate_xml_is_rejected(tmp_path):
    directory, hashes = _input(tmp_path, malformed_event=True)
    with pytest.raises(ValueError, match="Malformed IDSSE XML"):
        _audit(directory, hashes)


def test_source_pitch_dimensions_demand_explicit_review(tmp_path):
    directory, hashes = _input(tmp_path, pitch="107")
    with pytest.raises(ValueError, match="pitch dimensions"):
        _audit(directory, hashes)


@pytest.mark.parametrize("content", [
    (
        b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        b'<PutDataRequest>&xxe;</PutDataRequest>'
    ),
    b'<WrongRoot />',
])
def test_xml_entity_or_wrong_root_fails_closed(tmp_path, content):
    directory, hashes = _input(tmp_path)
    hashes["events"] = _file(directory, SOURCE_NAMES["events"], content)
    with pytest.raises(ValueError, match="Unsafe XML|Unexpected IDSSE XML root"):
        _audit(directory, hashes)


def test_streaming_sha256_uses_full_bytes_and_rejects_mutation(tmp_path):
    path = tmp_path / "fragment.xml"
    body = b"a" * (2 * 1024 * 1024 + 129)
    digest = _file(tmp_path, path.name, body)
    actual, size = sha256_file(path, digest)
    assert actual == digest and size == len(body)
    path.write_bytes(body + b"!")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        sha256_file(path, digest)


def test_no_network_or_cloud_dependency(tmp_path, monkeypatch):
    directory, hashes = _input(tmp_path)

    def no_http(*args, **kwargs):
        raise AssertionError("Source audit must remain local-only")
    monkeypatch.setattr("urllib.request.urlopen", no_http)
    assert not _audit(directory, hashes)["public_replay_enabled"]
