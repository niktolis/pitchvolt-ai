"""Cloud inference is never enabled by importing or constructing default config."""
import pytest

from matchpulse.foundry_adapter import FoundryConfig, FoundryDisabled, FoundryRoles


def test_foundry_inference_is_explicitly_opt_in() -> None:
    config = FoundryConfig(
        project_endpoint="https://example.services.ai.azure.com/api/projects/sample",
        model_deployment="unprovisioned",
    )
    with pytest.raises(FoundryDisabled, match="cost approval"):
        FoundryRoles(config)


def test_invalid_endpoint_or_empty_model_rejected_without_cloud_access() -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        FoundryConfig("http://example.com", "model")
    with pytest.raises(ValueError, match="deployment"):
        FoundryConfig("https://example.com", " ")
