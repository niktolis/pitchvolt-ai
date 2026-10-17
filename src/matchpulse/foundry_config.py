"""Single source of truth for developer-adjustable Foundry knobs.

Defaults and validation live here; provider code only applies these settings.
No credentials, secrets, or implicit inference approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class RoleSettings:
    max_output_tokens: int = 256
    reasoning_effort: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.max_output_tokens <= 1024:
            raise ValueError("Per-role output token cap must be between 1 and 1024")
        if self.reasoning_effort not in (None, "low", "medium", "high"):
            raise ValueError("Unsupported reasoning effort")



@dataclass(frozen=True)
class FoundryConfig:
    project_endpoint: str
    model_deployment: str
    inference_explicitly_approved: bool = False
    max_output_tokens_per_role: int = 256
    storyteller_model_deployment: str | None = None
    editorial_model_deployment: str | None = None
    max_inference_calls_per_narrative: int = 2
    analyst_settings: RoleSettings | None = None
    storyteller_settings: RoleSettings | None = None
    editorial_settings: RoleSettings | None = None
    max_tool_calls_per_analyst: int = 12
    max_prompt_characters: int = 12000
    timeout_seconds_per_role: float = 6.0

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
        if not 1 <= self.max_tool_calls_per_analyst <= 32:
            raise ValueError('Tool-call cap must be between 1 and 32')
        if not 256 <= self.max_prompt_characters <= 16000:
            raise ValueError('Prompt cap must be between 256 and 16000')
        if not 0.1 <= self.timeout_seconds_per_role <= 15:
            raise ValueError('Role timeout must be between 0.1 and 15 seconds')
        if self.max_inference_calls_per_narrative != 2:
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


