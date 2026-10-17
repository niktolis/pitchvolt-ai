"""Single source of truth for developer-adjustable Foundry knobs.

Defaults and validation live here; provider code only applies these settings.
No credentials, secrets, or implicit inference approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

# Foundry runtime configuration lives here. Other modules must not redefine
# defaults, limits, deployments, or the smoke experiment budget.
DEFAULT_OUTPUT_TOKENS = 256
MAX_OUTPUT_TOKENS = 8192
MIN_OUTPUT_TOKENS = 1
NARRATIVE_ROLE_CALLS = 2
DEFAULT_TOOL_CALL_LIMIT = 12
MAX_TOOL_CALL_LIMIT = 32
DEFAULT_PROMPT_CHARACTERS = 12000
MIN_PROMPT_CHARACTERS = 256
MAX_PROMPT_CHARACTERS = 16000
DEFAULT_ROLE_TIMEOUT_SECONDS = 6.0
MAX_ROLE_TIMEOUT_SECONDS = 15.0
MIN_ROLE_TIMEOUT_SECONDS = 0.1


@dataclass(frozen=True)
class SmokeSettings:
    """Single reviewed, non-billable-by-default local experiment configuration."""

    analyst_deployment: str = "matchpulse-gpt5-mini"
    storyteller_deployment: str = "matchpulse-gpt4o"
    analyst_output_tokens: int = 4096
    http_max_retries: int = 2
    role_level_retries: int = 0
    timeout_seconds_per_role: float = MAX_ROLE_TIMEOUT_SECONDS
    audience: str = "analyst"
    scenario: str = "high_press"


SMOKE_SETTINGS = SmokeSettings()


@dataclass(frozen=True)
class RoleSettings:
    max_output_tokens: int = DEFAULT_OUTPUT_TOKENS
    reasoning_effort: str | None = None

    def __post_init__(self) -> None:
        if not MIN_OUTPUT_TOKENS <= self.max_output_tokens <= MAX_OUTPUT_TOKENS:
            raise ValueError("Per-role output token cap must be between 1 and 8192")
        if self.reasoning_effort not in (None, "low", "medium", "high"):
            raise ValueError("Unsupported reasoning effort")



@dataclass(frozen=True)
class FoundryConfig:
    project_endpoint: str
    model_deployment: str
    inference_explicitly_approved: bool = False
    max_output_tokens_per_role: int = DEFAULT_OUTPUT_TOKENS
    storyteller_model_deployment: str | None = None
    editorial_model_deployment: str | None = None
    max_inference_calls_per_narrative: int = NARRATIVE_ROLE_CALLS
    analyst_settings: RoleSettings | None = None
    storyteller_settings: RoleSettings | None = None
    editorial_settings: RoleSettings | None = None
    max_tool_calls_per_analyst: int = DEFAULT_TOOL_CALL_LIMIT
    max_prompt_characters: int = DEFAULT_PROMPT_CHARACTERS
    timeout_seconds_per_role: float = DEFAULT_ROLE_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        parsed = urlsplit(self.project_endpoint)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Foundry endpoint must be a clean HTTPS project URL")
        if not parsed.hostname.endswith(".services.ai.azure.com"):
            raise ValueError("Foundry endpoint must target the Foundry project domain")
        RoleSettings(max_output_tokens=self.max_output_tokens_per_role)
        if not 1 <= self.max_tool_calls_per_analyst <= MAX_TOOL_CALL_LIMIT:
            raise ValueError('Tool-call cap must be between 1 and 32')
        if not MIN_PROMPT_CHARACTERS <= self.max_prompt_characters <= MAX_PROMPT_CHARACTERS:
            raise ValueError('Prompt cap must be between 256 and 16000')
        if not MIN_ROLE_TIMEOUT_SECONDS <= self.timeout_seconds_per_role <= MAX_ROLE_TIMEOUT_SECONDS:
            raise ValueError('Role timeout must be between 0.1 and 15 seconds')
        if self.max_inference_calls_per_narrative != NARRATIVE_ROLE_CALLS:
            raise ValueError("Two-role narrative must have exactly two inference calls")
        for deployment in (
            self.model_deployment,
            self.storyteller_model_deployment,
            self.editorial_model_deployment,
        ):
            if deployment is not None and not deployment.strip():
                raise ValueError("Foundry deployment name is required")

    def settings_for(self, role: str) -> RoleSettings:
        if role not in ("analyst", "storyteller", "editorial"):
            raise ValueError("Unknown specialist role")
        custom = getattr(self, f"{role}_settings")
        return custom if custom is not None else RoleSettings(
            max_output_tokens=self.max_output_tokens_per_role
        )

    @property
    def role_deployments(self) -> dict[str, str]:
        """Configured clients; Editorial is prepared but never scheduled."""
        return {
            "analyst": self.model_deployment,
            "storyteller": self.storyteller_model_deployment or self.model_deployment,
            **(
                {"editorial": self.editorial_model_deployment}
                if self.editorial_model_deployment is not None
                else {}
            ),
        }


