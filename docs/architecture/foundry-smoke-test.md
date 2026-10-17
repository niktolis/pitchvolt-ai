# Isolated two-role Foundry smoke test (issue #4)

This is **not** the production SSE integration. It runs one synthetic high-press insight
through the existing read-only evidence port, deployed Analyst, deployed Storyteller,
and deterministic verification. The default is **offline dry-run**.

## One-time workstation setup

1. Merge the reviewed smoke PR and pull latest `main`.
2. Install `uv` and Azure CLI if not already available.
3. From the repository root: `uv sync --frozen --extra dev --extra foundry`.
4. Authenticate your user interactively: `az login`; then check the correct subscription
   with `az account show --query '{name:name,id:id}'`. Never paste access tokens or keys.
5. Copy **your own project endpoint** from Microsoft Foundry project overview. It should
   look like `https://<account>.services.ai.azure.com/api/projects/<project>`.
   Set `MATCHPULSE_FOUNDRY_PROJECT_ENDPOINT` to that URL. The project endpoint is
   **not** the `.../openai/v1/` model-inference base URL shown on a deployment page.
   Role-based authorization for the signed-in identity may be required.

## Commands

```bash
uv run --frozen --extra foundry python -m matchpulse.foundry_smoke

# Only after reviewing the dry run and verifying the endpoint/active Azure account:
uv run --frozen --extra foundry python -m matchpulse.foundry_smoke --execute --acknowledge-billable-inference
```

Under fish shell, set the endpoint with:
```fish
set -x MATCHPULSE_FOUNDRY_PROJECT_ENDPOINT 'https://<account>.services.ai.azure.com/api/projects/<project>'
```

No secrets belong in source, CLI history, screenshots, PR comments or test reports.
`DefaultAzureCredential` uses your existing local identity; use `az login` if necessary.
Do not invoke the live command twice without separate authorization: an SDK failure,
timeout or fallback can still incur token charges, even when the report shows no usage.

### Hard boundaries and diagnostics

- Only **one** fixture insight and a fresh `FoundryRoles` instance per invocation.
- Local ceiling: one Analyst `Agent.run` and one Storyteller `Agent.run`. If the
  Analyst fails validation, the Storyteller is not invoked. No Editorial role.
- No automatic retries by this harness. However the SDK may internally retry or
  perform additional model calls during a tool loop. **This is not an API-request or
  monetary hard cap.** Azure rate limits and credit balance should be checked separately.
- Returns nonzero unless both roles, model-initiated evidence retrieval, and final
  verified publication succeeded. Reports observable SDK token counts (if available),
  durations and evidence IDs; missing SDK usage is not proof of zero consumption.
- Do not change `MATCHPULSE_NARRATIVE_PROVIDER`, application SSE opt-in or Azure
  resource settings; the usual application path stays deterministic/offline.
- A 1,000 TPM allocation on each deployment may be insufficient for a single
  GPT-5 mini tool-calling run. 15-second local timeout likewise may be insufficient.
  If the first run fails for rate limit, incomplete output or SDK incompatibility,
  **stop** and report sanitized results before any modification or second billable test.
- A successful output proves this one fixture only, not general runtime correctness.

### Expected result

Dry run prints `"mode": "DRY_RUN"` and makes no Azure calls.
Live run prints two invocations, a nonempty `model_initiated_evidence_tool_calls`
matching the expected IDs, `"source": "controlled"`, and `PASS`.
A fallback, structured-output failure, SDK or auth error returns nonzero.
