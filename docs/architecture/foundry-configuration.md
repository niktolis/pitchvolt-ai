# Foundry configuration knobs (developer guide)

**Source of truth:** `src/pitchvolt/foundry_config.py`. Do not duplicate tunables or validation in the adapter. `FoundryConfig` and `RoleSettings` are immutable typed dataclasses. Existing imports through `pitchvolt.foundry_adapter` remain supported.

| Setting | Default | Valid range / intent |
|---|---:|---|
| `max_output_tokens_per_role` | 256 | 1–1024 requested output tokens per role; legacy fallback |
| `analyst_settings`, `storyteller_settings`, `editorial_settings` | None | Override individual roles with `RoleSettings` |
| `RoleSettings.max_output_tokens` | 256 | 1–1024 requested output tokens |
| `RoleSettings.reasoning_effort` | None | low/medium/high allowed in config; **non-None blocked at runtime pending actual SDK verification** |
| `max_inference_calls_per_narrative` | 2 | Exactly 2 (Analyst + Storyteller); not a global spend limiter |
| `max_tool_calls_per_analyst` | 12 | 1–32 local evidence retrieval invocations |
| `max_prompt_characters` | 12000 | 256–16000 Unicode characters; **not a token limit** |
| `timeout_seconds_per_role` | 6.0 | 0.1–15 seconds per role; timeout does not cancel already charged service work |
| `inference_explicitly_approved` | False | Explicit gate; **do not set true without separate user approval** |
| `model_deployment` | required | Analyst deployment; Storyteller inherits only for single-model baseline |
| `storyteller_model_deployment`, `editorial_model_deployment` | None | Optional separate deployments; Editorial remains unscheduled |

Example (offline configuration only):

```python
from pitchvolt.foundry_config import FoundryConfig, RoleSettings

config = FoundryConfig(
    project_endpoint="https://example.services.ai.azure.com/api/projects/sample",
    model_deployment="analyst-model",
    storyteller_model_deployment="storyteller-model",
    analyst_settings=RoleSettings(max_output_tokens=512),
    storyteller_settings=RoleSettings(max_output_tokens=128),
    max_tool_calls_per_analyst=8,
    timeout_seconds_per_role=4.0,
)  # inference remains disabled
```

**Precedence:** explicitly supplied role settings override the legacy common output cap; otherwise that cap applies. The application's `narrative_stream.py` still sets Foundry inference approval to false regardless of environment variables. No secrets should appear in config files. These are local safety controls, not guaranteed Azure rate or monetary ceilings.

**Standing rule (all new code):** developer-configurable knobs belong to one typed, documented configuration module per subsystem, with units/defaults/ranges, explicit precedence and validation. Avoid scattering literals across domain, adapter, tests and docs. Share canonical schemas and DRY helpers without unnecessary indirection; changing safety ceilings must be reviewed.
