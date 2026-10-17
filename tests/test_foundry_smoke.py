"""The isolated Foundry smoke command must be offline by default."""
import asyncio

import pytest

from matchpulse import foundry_smoke


def test_smoke_dry_run_requires_no_sdk_or_endpoint(capsys) -> None:
    assert asyncio.run(foundry_smoke.run([])) == 0
    output = capsys.readouterr().out
    assert '"mode": "DRY_RUN"' in output
    assert "No Azure credentials loaded" in output


def test_smoke_requires_explicit_two_part_live_opt_in() -> None:
    with pytest.raises(SystemExit, match="acknowledge-billable-inference"):
        asyncio.run(foundry_smoke.run(["--execute"]))


def test_smoke_uses_single_real_synthetic_bundle() -> None:
    bundle = foundry_smoke.fixture()
    assert bundle.events
    assert tuple(event.event_id for event in bundle.events) == (
        bundle.insight.evidence_event_ids
    )
