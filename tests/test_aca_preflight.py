"""Cloud rollout preflight must be offline and reject risky configuration."""
import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "aca-preflight.sh"

BASE = {
    "AZURE_RESOURCE_GROUP": "rg-matchpulse-demo",
    "AZURE_CONTAINER_APP": "matchpulse-web",
    "AZURE_CONTAINER_ENV": "matchpulse-demo-env",
    "AZURE_REGION": "swedencentral",
    "AZURE_IMAGE": "example.azurecr.io/matchpulse@sha256:" + "a" * 64,
    "AZURE_REGISTRY_SERVER": "example.azurecr.io",
}


def preflight(**overrides: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **BASE, **overrides}
    return subprocess.run(
        ["bash", str(SCRIPT)], env=env, capture_output=True, text=True, check=False
    )


def test_preflight_describes_only_offline_plan() -> None:
    result = preflight()
    assert result.returncode == 0
    assert "DRY_RUN: no Azure resources created or modified" in result.stdout
    assert "Provider: local" in result.stdout
    assert "Min replicas: 0" in result.stdout


def test_preflight_refuses_remote_inference() -> None:
    result = preflight(MATCHPULSE_NARRATIVE_PROVIDER="foundry")
    assert result.returncode != 0


def test_preflight_refuses_mutable_images() -> None:
    result = preflight(AZURE_IMAGE="example.azurecr.io/matchpulse:latest")
    assert result.returncode != 0


def test_preflight_refuses_unapproved_replica_bounds() -> None:
    result = preflight(AZURE_MAX_REPLICAS="10")
    assert result.returncode != 0
