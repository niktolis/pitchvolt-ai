# Foundry configuration knobs (developer guide)

**Source of truth:** `src/pitchvolt/foundry_config.py`. Do not duplicate tunables or validation in the adapter. `FoundryConfig` and `RoleSettings` are immutable typed dataclasses. Existing imports through `pitchvolt.foundry_adapter` remain supported.

| Setting | Default | Valid range / intent |
|---|---:|---|
| `max_output_tokens_per_role` | 256 | 1–8192 requested output tokens per role; legacy fallback |
| `analyst_settings`, `storyteller_settings`, `editorial_settings` | None | Override individual roles with `RoleSettings` |
| `RoleSettings.max_output_tokens` | 256 | 1–8192 requested output tokens |
| `RoleSettings.reasoning_effort` | None | low/medium/high allowed in config; **non-None blocked at runtime pending actual SDK verification** |
| `max_inference_calls_per_narrative` | 2 | Exactly 2 (Analyst + Storyteller); not a global spend limiter |
| `max_tool_calls_per_analyst` | 12 | 1–32 local evidence retrieval invocations |
| `max_prompt_characters` | 12000 | 256–16000 Unicode characters; **not a token limit** |
| `timeout_seconds_per_role` | 6.0 | 0.1–30 seconds per role; timeout does not cancel already charged service work |
| `inference_explicitly_approved` | False | Explicit gate; true only for the standing-authorized merge CI smoke, or an independently approved exceptional run |
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

For the isolated **merge-only CI and optional local debugging smoke**:
`SMOKE_SETTINGS.analyst_output_tokens=6144`,
`SMOKE_SETTINGS.storyteller_output_tokens=1024`,
`SMOKE_SETTINGS.timeout_seconds_per_role=30`,
`SMOKE_SETTINGS.http_max_retries=0`,
no role-level retries. The localhost preview shares these smoke settings
but remains separately disabled by default. No monetary ceiling is implied.
`foundry_preflight` checks configuration and installed SDK metadata offline
without constructing a provider or requesting Azure credentials.

Verified existing Azure deployment names are `matchpulse-gpt5-mini` (GPT-5 mini Global Standard) and `matchpulse-gpt4o` (GPT-4o Standard), both provisioned in Sweden Central. Do not create replacement deployments for PitchVolt branding. Normal production output defaults remain 256 tokens.

**Automatic inference policy:** reviewed/merged PR events authorize one isolated smoke run through GitHub Actions. The CLI keeps its deliberate `--execute --acknowledge-billable-inference` flags; the merge-only job supplies these flags as a machine-enforced standing authorization. The public production path remains Foundry-disabled. See [merge runbook](foundry-smoke-test.md).
