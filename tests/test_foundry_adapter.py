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
        FoundryConfig("https://example.services.ai.azure.com", " ")


@pytest.mark.parametrize("endpoint", [
    "https://evil.example.com",
    "https://user:password@example.services.ai.azure.com",
    "https://example.services.ai.azure.com?token=secret",
    "http://example.services.ai.azure.com",
    "https://example.services.ai.azure.com#fragment",
])
def test_foundry_endpoint_must_be_project_scoped_and_secret_free(endpoint: str) -> None:
    with pytest.raises(ValueError, match="endpoint"):
        FoundryConfig(endpoint, "model")


@pytest.mark.parametrize("cap", [0, 1025])
def test_excessive_or_invalid_output_token_budget_is_rejected(cap: int) -> None:
    with pytest.raises(ValueError, match="token cap"):
        FoundryConfig(
            "https://example.services.ai.azure.com",
            "model",
            max_output_tokens_per_role=cap,
        )


def test_maximum_number_of_roles_is_fixed() -> None:
    with pytest.raises(ValueError, match="two inference calls"):
        FoundryConfig(
            "https://example.services.ai.azure.com",
            "model",
            max_inference_calls_per_narrative=3,
        )


def test_valid_disabled_foundry_configuration_has_zero_side_effects() -> None:
    config = FoundryConfig(
        "https://example.services.ai.azure.com",
        "not-provisioned",
        max_output_tokens_per_role=192,
    )
    assert not config.inference_explicitly_approved
    assert config.max_inference_calls_per_narrative == 2
    with pytest.raises(FoundryDisabled, match="cost approval"):
        FoundryRoles(config)


def test_independent_deployments_validate_without_enabling_inference() -> None:
    config = FoundryConfig(
        "https://example.services.ai.azure.com/api/projects/sample",
        "analyst-gpt5-mini",
        storyteller_model_deployment="storyteller-gpt4o-mini",
        editorial_model_deployment="editorial-not-enabled",
    )
    assert config.role_deployments == {
        "analyst": "analyst-gpt5-mini",
        "storyteller": "storyteller-gpt4o-mini",
        "editorial": "editorial-not-enabled",
    }
    with pytest.raises(FoundryDisabled, match="cost approval"):
        FoundryRoles(config)


def test_empty_optional_role_deployment_rejected() -> None:
    with pytest.raises(ValueError, match="deployment"):
        FoundryConfig("https://example.services.ai.azure.com", "analyst",
                      storyteller_model_deployment=" ")
    with pytest.raises(ValueError, match="deployment"):
        FoundryConfig("https://example.services.ai.azure.com", "analyst",
                      editorial_model_deployment="")
