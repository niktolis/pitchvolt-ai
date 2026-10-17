"""Deployment rollout instructions must never mutate Azure by themselves."""
import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "aca-rollout-plan.sh"


def test_rollout_plan_requires_subscription_and_prints_only() -> None:
    env = {
        **os.environ,
        "AZURE_SUBSCRIPTION_ID": "example-sub",
        "AZURE_RESOURCE_GROUP": "rg-matchpulse-demo",
        "AZURE_REGION": "swedencentral",
        "AZURE_REGISTRY_NAME": "matchpulsereg",
        "AZURE_CONTAINER_ENV": "matchpulse-env",
        "AZURE_CONTAINER_APP": "matchpulse-web",
        "MATCHPULSE_NARRATIVE_PROVIDER": "local",
    }
    result = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert result.returncode == 0
    assert "DOES NOT execute Azure changes" in result.stdout
    assert "az acr create" in result.stdout
    assert "az containerapp env create" in result.stdout


def test_rollout_plan_rejects_remote_provider() -> None:
    env = {
        **os.environ,
        "AZURE_SUBSCRIPTION_ID": "example-sub",
        "AZURE_RESOURCE_GROUP": "rg-matchpulse-demo",
        "AZURE_REGION": "swedencentral",
        "AZURE_REGISTRY_NAME": "matchpulsereg",
        "AZURE_CONTAINER_ENV": "matchpulse-env",
        "AZURE_CONTAINER_APP": "matchpulse-web",
        "MATCHPULSE_NARRATIVE_PROVIDER": "foundry",
    }
    result = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert result.returncode != 0
