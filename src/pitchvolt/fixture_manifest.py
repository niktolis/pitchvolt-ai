"""Pinned football replay fixture manifest, independent of provider adapter.

A fixture manifest describes whether the underlying records are actual Open
Data or originally synthetic. It is not a match import or license grant.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FixtureOrigin(StrEnum):
    STATSBOMB_OPEN_DATA = "statsbomb_open_data"
    PITCHVOLT_SYNTHETIC = "pitchvolt_synthetic"


class FixtureManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    fixture_id: str = Field(min_length=1)
    origin: FixtureOrigin
    match_id: str = Field(min_length=1)
    event_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    event_count: int = Field(gt=0)
    match_duration_ms: int = Field(gt=0)
    event_coverage: str = Field(pattern=r"^(full_match|excerpt)$")
    source_url: str | None = None
    attribution: str | None = None
    generator_seed: int | None = None

    @model_validator(mode="after")
    def require_origin_specific_traceability(self) -> FixtureManifest:
        if self.origin == FixtureOrigin.STATSBOMB_OPEN_DATA:
            if (
                not self.source_url
                or not self.source_url.startswith("https://github.com/hudl/open-data/")
                or not self.attribution
                or self.generator_seed is not None
            ):
                raise ValueError("Real StatsBomb Open Data requires official source and attribution")
        elif self.source_url is not None or self.generator_seed is None:
            raise ValueError("Synthetic fixture requires seed and must not claim Open Data provenance")
        return self
