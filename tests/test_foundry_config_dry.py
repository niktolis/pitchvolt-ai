"""Configuration is the only owner of Foundry defaults and effective smoke settings."""
import pytest

from matchpulse.foundry_config import (
    DEFAULT_OUTPUT_TOKENS,
    MAX_OUTPUT_TOKENS,
    NARRATIVE_ROLE_CALLS,
    SMOKE_SETTINGS,
    FoundryConfig,
    RoleSettings,
    isolated_foundry_config,
)


def test_one_config_controls_smoke_and_preview() -> None:
    endpoint = "https://example.services.ai.azure.com/api/projects/offline"
    config = isolated_foundry_config(
        endpoint, evidence_event_count=6, inference_approved=True
    )
    assert config.model_deployment == SMOKE_SETTINGS.analyst_deployment
    assert config.storyteller_model_deployment == SMOKE_SETTINGS.storyteller_deployment
    assert config.settings_for("analyst").max_output_tokens == SMOKE_SETTINGS.analyst_output_tokens
    assert config.timeout_seconds_per_role == SMOKE_SETTINGS.timeout_seconds_per_role
    assert config.max_tool_calls_per_analyst == 6
    assert config.max_inference_calls_per_narrative == NARRATIVE_ROLE_CALLS


def test_default_policy_is_not_billable_and_has_no_smoke_override() -> None:
    endpoint = "https://example.services.ai.azure.com/api/projects/offline"
    assert not isolated_foundry_config(endpoint, evidence_event_count=1).inference_explicitly_approved
    assert RoleSettings().max_output_tokens == DEFAULT_OUTPUT_TOKENS
    assert FoundryConfig(endpoint, "offline").settings_for("analyst").max_output_tokens == DEFAULT_OUTPUT_TOKENS
    assert SMOKE_SETTINGS.analyst_output_tokens <= MAX_OUTPUT_TOKENS
    with pytest.raises(ValueError, match="nonempty"):
        isolated_foundry_config(endpoint, evidence_event_count=0)


def test_no_redefined_smoke_policy_in_callers() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "src" / "matchpulse"
    for name in ("foundry_smoke.py", "foundry_preview.py"):
        source = (root / name).read_text()
        assert "SMOKE_ANALYST_OUTPUT_TOKENS =" not in source
        assert "ANALYST_DEPLOYMENT =" not in source
        assert "FoundryConfig(" not in source
        assert "isolated_foundry_config(" in source
