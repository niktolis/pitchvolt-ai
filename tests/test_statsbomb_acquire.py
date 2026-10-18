"""Offline acquisition and immutable manifest compatibility tests."""
import json

import pytest

from pitchvolt.providers.statsbomb_historical import load_historical_fixture
from pitchvolt.statsbomb_acquire import prepare_fixture, source_urls

COMMIT = "a" * 40


def records():
    return [
        {"id": "event-1", "index": 1, "period": 1,
         "timestamp": "00:00:01.000", "minute": 0, "second": 1,
         "type": {"id": 30, "name": "Pass"}},
        {"id": "event-2", "index": 2, "period": 2,
         "timestamp": "00:45:01.000", "minute": 90, "second": 1,
         "type": {"id": 34, "name": "Half End"}},
    ]


def test_source_url_is_pinned_to_official_repository():
    raw, official = source_urls(COMMIT, "123")
    assert raw == f"https://raw.githubusercontent.com/hudl/open-data/{COMMIT}/data/events/123.json"
    assert official == f"https://github.com/hudl/open-data/blob/{COMMIT}/data/events/123.json"


@pytest.mark.parametrize("commit,match_id", [
    ("master", "123"),
    ("a" * 40, "../secret"),
    ("a" * 40, "https://elsewhere.invalid"),
    ("B" * 40, "123"),
])
def test_reject_unpinned_or_unsafe_source(commit, match_id):
    with pytest.raises(ValueError):
        source_urls(commit, match_id)


def test_acquire_then_reopen_with_provenance(tmp_path):
    original = json.dumps(records()).encode("utf-8")
    manifest = prepare_fixture(original, commit=COMMIT, match_id="123", directory=tmp_path)
    assert manifest.event_count == 2
    assert manifest.event_coverage == "excerpt"
    assert manifest.event_sha256
    assert (tmp_path / "123.json").read_bytes() == original
    read = load_historical_fixture(tmp_path / "123.json", manifest)
    assert read.presentation_count == 1
    assert read.supported_count == 1
    assert read.unreviewed_count == 0
    with pytest.raises(FileExistsError):
        prepare_fixture(original, commit=COMMIT, match_id="123", directory=tmp_path)


def test_incomplete_match_marked_excerpt(tmp_path):
    manifest = prepare_fixture(
        json.dumps(records()[:1]).encode(), commit=COMMIT, match_id="123",
        directory=tmp_path,
    )
    assert manifest.event_coverage == "excerpt"
