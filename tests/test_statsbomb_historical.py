"""Regression gates for the lossless historical input boundary."""
import hashlib
import json

import pytest

from matchpulse.fixture_manifest import FixtureManifest, FixtureOrigin
from matchpulse.providers.statsbomb_historical import load_historical_fixture


def make_fixture(tmp_path, records):
    raw = json.dumps(records).encode("utf-8")
    path = tmp_path / "123.json"
    path.write_bytes(raw)
    manifest = FixtureManifest(
        fixture_id="historical-123",
        origin=FixtureOrigin.STATSBOMB_OPEN_DATA,
        match_id="123",
        event_sha256=hashlib.sha256(raw).hexdigest(),
        event_count=len(records),
        match_duration_ms=5_400_000,
        event_coverage="full_match",
        source_url="https://github.com/hudl/open-data/blob/master/data/events/123.json",
        attribution="StatsBomb Open Data",
    )
    return path, manifest


def event(index, kind):
    return {
        "id": f"test-uuid-{index}",
        "index": index,
        "period": 1,
        "timestamp": "00:00:00.000",
        "type": {"id": index, "name": kind},
        "team": {"id": 1, "name": "Recorded team"},
    }


def test_historical_records_preserved_and_unreviewed_counted(tmp_path):
    records = [event(1, "Starting XI"), event(2, "Pass"), event(3, "Foul Committed")]
    path, manifest = make_fixture(tmp_path, records)
    loaded = load_historical_fixture(path, manifest)
    assert list(loaded.records) == records
    assert loaded.supported_count == 1
    assert loaded.presentation_count == 1
    assert loaded.unreviewed_count == 1
    assert not loaded.coverage_complete_for_projection
    assert loaded.event_counts["Foul Committed"] == 1


def test_hash_mismatch_fails_closed(tmp_path):
    path, manifest = make_fixture(tmp_path, [event(1, "Pass")])
    path.write_text(json.dumps([event(1, "Shot")]))
    with pytest.raises(ValueError, match="SHA-256"):
        load_historical_fixture(path, manifest)


def test_synthetic_rejected_by_historical_loader(tmp_path):
    path, manifest = make_fixture(tmp_path, [event(1, "Pass")])
    synthetic = manifest.model_copy(update={
        "origin": FixtureOrigin.MATCHPULSE_SYNTHETIC, "source_url": None,
        "generator_seed": 42,
    })
    with pytest.raises(ValueError, match="origin"):
        load_historical_fixture(path, synthetic)


def test_wrong_event_count_rejected(tmp_path):
    path, manifest = make_fixture(tmp_path, [event(1, "Pass")])
    incorrect = manifest.model_copy(update={"event_count": 2})
    with pytest.raises(ValueError, match="count"):
        load_historical_fixture(path, incorrect)


def test_duplicate_ids_rejected(tmp_path):
    records = [event(1, "Pass"), event(2, "Carry")]
    records[1]["id"] = records[0]["id"]
    path, manifest = make_fixture(tmp_path, records)
    with pytest.raises(ValueError, match="duplicate"):
        load_historical_fixture(path, manifest)
