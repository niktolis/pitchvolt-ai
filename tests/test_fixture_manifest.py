"""Open Data and synthetic replay fixtures must not share provenance."""
import pytest
from pydantic import ValidationError

from pitchvolt.fixture_manifest import FixtureManifest, FixtureOrigin

BASE = {
    "fixture_id": "match-1",
    "match_id": "match-1",
    "event_sha256": "a" * 64,
    "event_count": 400,
    "match_duration_ms": 5_400_000,
    "event_coverage": "full_match",
}


def test_real_open_data_requires_attribution_and_pinned_source() -> None:
    actual = FixtureManifest(
        **BASE,
        origin=FixtureOrigin.STATSBOMB_OPEN_DATA,
        source_url="https://github.com/hudl/open-data/blob/master/data/events/123.json",
        attribution="StatsBomb Open Data",
    )
    assert actual.generator_seed is None
    with pytest.raises(ValidationError):
        FixtureManifest(**BASE, origin=FixtureOrigin.STATSBOMB_OPEN_DATA)
    with pytest.raises(ValidationError):
        FixtureManifest(**BASE, origin=FixtureOrigin.STATSBOMB_OPEN_DATA,
                        source_url="https://example.org/events.json",
                        attribution="StatsBomb Open Data")


def test_synthetic_cannot_claim_historical_source() -> None:
    synthetic = FixtureManifest(
        **BASE, origin=FixtureOrigin.PITCHVOLT_SYNTHETIC, generator_seed=42
    )
    assert synthetic.origin == FixtureOrigin.PITCHVOLT_SYNTHETIC
    with pytest.raises(ValidationError):
        FixtureManifest(**BASE, origin=FixtureOrigin.PITCHVOLT_SYNTHETIC,
                        generator_seed=42,
                        source_url="https://github.com/hudl/open-data/blob/master/data/events/123.json")
    with pytest.raises(ValidationError):
        FixtureManifest(**BASE, origin=FixtureOrigin.PITCHVOLT_SYNTHETIC)


def test_corpus_manifest_requires_hash_and_explicit_coverage() -> None:
    with pytest.raises(ValidationError):
        FixtureManifest(**{**BASE, "event_sha256": "unverified"},
                        origin=FixtureOrigin.PITCHVOLT_SYNTHETIC, generator_seed=42)
    with pytest.raises(ValidationError):
        FixtureManifest(**{**BASE, "event_coverage": "unknown"},
                        origin=FixtureOrigin.PITCHVOLT_SYNTHETIC, generator_seed=42)
