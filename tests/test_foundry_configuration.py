"""Developer knob definitions remain in the dedicated typed config module."""
import pytest

from matchpulse.foundry_adapter import FoundryConfig as PublicFoundryConfig
from matchpulse.foundry_config import FoundryConfig, RoleSettings


def test_adapter_reexports_canonical_settings() -> None:
    assert FoundryConfig is PublicFoundryConfig


def test_role_overrides_are_explicit_and_defaults_remain_safe() -> None:
    config = FoundryConfig(
        "https://example.services.ai.azure.com/api/projects/demo",
        "analyst-model",
        storyteller_model_deployment="storyteller-model",
        max_output_tokens_per_role=192,
        analyst_settings=RoleSettings(max_output_tokens=512),
    )
    assert config.settings_for("analyst").max_output_tokens == 512
    assert config.settings_for("storyteller").max_output_tokens == 192
    assert config.max_tool_calls_per_analyst == 12
    assert config.timeout_seconds_per_role == 6.0
    assert not config.inference_explicitly_approved


@pytest.mark.parametrize("setting,value", [
    ("max_tool_calls_per_analyst", 0),
    ("max_prompt_characters", 100),
    ("timeout_seconds_per_role", 0),
])
def test_invalid_tunable_is_rejected_at_construction(setting: str, value: int) -> None:
    with pytest.raises(ValueError):
        FoundryConfig(
            "https://example.services.ai.azure.com/api/projects/demo",
            "analyst-model", **{setting: value},
        )
