# Foundry role-specific budgets and observation

Each specialist now supports `RoleSettings(max_output_tokens, reasoning_effort)` independently via `FoundryConfig.analyst_settings`, `storyteller_settings` and `editorial_settings`. Unset settings inherit the previous 256-token cap. Defaults preserve the two-inference-call Analyst/Storyteller workflow and leave Editorial unscheduled.

`FoundryRoles.invocations` tracks per-completed-call role, deployment, elapsed milliseconds and SDK-reported token counts when exposed in the expected shape. Missing usage is **unknown**, never estimated as zero. This local record is not currently surfaced through the SSE API or exported to Azure telemetry. It is a low-level diagnostic foundation, not comprehensive observability.

**SDK compatibility safeguard:** non-default `reasoning_effort` is validated as a configured intent but deliberately rejected before calling the SDK until the actual SDK model-specific options are verified in a bounded live test. No unsupported reasoning parameter is silently passed to models. The per-role output cap limits only requested generated tokens; total spend, input tokens, tool turns, response retries, and concurrency remain separately unbounded until additional enforcement is added.

Foundry model inference continues to be disabled in `narrative_stream.py`. Tests are offline SDK doubles. No Azure provisioning or paid inference is performed by this change.
