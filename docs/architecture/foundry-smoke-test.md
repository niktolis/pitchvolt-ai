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
The isolated smoke harness uses **`AzureCliCredential`**, which relies on `az login` and does not probe local Managed Identity endpoints. General application credentials are unchanged. A hanging Azure CLI token request or SDK network call may still need manual interruption.
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

### First live attempt diagnostic (17 Oct 2026)

The first test was interrupted inside `DefaultAzureCredential` -> Managed Identity IMDS token acquisition, before a confirmed model response. Azure CLI independently obtained an access token, and the project endpoint was correct. **Do not rerun billable inference automatically** after updating this branch: inspect Azure model metrics/usage and confirm a new invocation is explicitly authorized. The fix scopes Azure CLI authentication to this workstation smoke harness only.

### Sanitized provider failures

When the SDK raises a provider exception, the smoke command prints an allowlisted
exception type, optional exception cause class, optional numeric HTTP status and
known-safe error code. It deliberately never prints raw exception strings, headers,
request bodies, access tokens or response bodies. HTTP status helps distinguish
400 (request contract), 401/403 (auth), 404 (deployment/endpoint) and 429
(quota/rate). If code/status is unavailable, stop and investigate locally rather
than rerunning inference. No new authorization is implied by a diagnostic PR.

### Agent Framework ChatOptions compatibility

Installed Agent Framework Core 1.22.0 declares `ChatOptions.max_tokens` and `response_format`, not `ChatOptions.max_output_tokens`. The provider maps the existing configured output budget to the supported `max_tokens` request option. This fixes an offline-confirmed contract mismatch, **not** a confirmed explanation for earlier `ChatClientException` without HTTP metadata. No renewed billable test is authorized by this change.

### Third live smoke and offline response diagnostics

The 17 Oct Analyst request returned in ~5.3 seconds without a structured value or model-initiated evidence tool calls. The deterministic fallback correctly rejected the ungrounded result and the Storyteller was not invoked. SDK response metadata (allowed completion status/finish reason, message count, structured-value presence and optional token counters) is now reported without exposing model output, raw payload or credentials. Absence of usage counters must not be interpreted as zero billing. Inspect this metadata before considering a change to the Analyst token budget. Neither this diagnostics update nor a local dry run authorizes more billable inference.

### Isolated Analyst budget experiment (not a live-test approval)

For a future separately approved smoke attempt, the CLI now specifies 512 output tokens for the GPT-5 mini Analyst instead of the default 256, while the Storyteller and production defaults remain at 256. The previous Analyst returned no structured value and no tool calls, but token exhaustion has **not** been proven. GPT-5 reasoning tokens may consume part of the response budget. The larger cap may increase cost or encounter the deployment's 1,000 TPM throughput constraints; do not increase Azure quota or execute inference without separate operator approval. The CLI dry run displays the proposed budget without Azure requests.

### Local OpenAI HTTP retry policy

The explicitly invoked smoke harness injects an `AIProjectClient` whose
`get_openai_client()` passes `max_retries=0` to the OpenAI SDK. This removes
transparent HTTP retries (normally two) for this test only. The ordinary
application adapter continues to use default SDK client construction. Model
function/tool rounds can still cause multiple HTTP requests, and removing
retries does not guarantee that Azure will cease issuing HTTP 429 responses.
No production quota, inference permission, or monetary cap is changed.

### Async client compatibility correction

For the isolated manual smoke, use `azure.ai.projects.aio.AIProjectClient` and
`azure.identity.aio.AzureCliCredential`. The asynchronous project client
returns an authenticated `openai.AsyncOpenAI` for the Agent Framework's
async `RawOpenAIChatClient`. Its smoke-only factory override sets
`max_retries=0`. The earlier sync `azure.ai.projects.AIProjectClient`
returned `openai.OpenAI` and triggered a wrapped `TypeError` in the
async execution path. A real installed-SDK constructor test runs offline in
Python CI and verifies **both** role clients, transport type and retry setting.
Production construction and the 20,000 TPM Azure capacity are unchanged. No
inference is authorized or run by the offline test.

### Manual application/SSE integration preview

The existing public `/api/matches/{name}/narratives/stream` remains locally
deterministic. A **separate, non-OpenAPI, localhost-only** route is provided for
an explicitly authorized operator demonstration:

`GET /api/matches/high_press/narratives/foundry-preview/stream?audience=analyst`

No production, CI, or normal application request enables this path.
The operator must separately set
`MATCHPULSE_FOUNDRY_PREVIEW_ENABLED=true`, a random, private
`MATCHPULSE_FOUNDRY_PREVIEW_TOKEN` (at least 32 characters), and the
existing `MATCHPULSE_FOUNDRY_PROJECT_ENDPOINT`. The HTTP request must
originate from localhost and carry `X-MatchPulse-Inference-Token` with
the exact value. Keep the token outside shell history, source control,
logs, URLs and screenshots. A fresh local server process accepts at most
**one** authorized HTTP preview request; concurrent/repeated requests
return HTTP 429. Restarting, scaling or running additional processes
resets the per-process guard: **this is not a global financial cap**.
Do not expose this demonstration endpoint through a proxy or deploy it
with its opt-in environment setting enabled.

The authorized route runs at most one tactical insight through the same
async Azure CLI credential / Foundry client and two-role orchestrator
validated in the standalone smoke test. HTTP transport retries are
disabled, the Analyst output cap remains 512, and each role is limited
to one invocation (SDK tool rounds may still consume additional requests).
The existing deterministic verifier produces the publishable narrative;
provider failure returns evidence-backed fallback, not unverified prose.
Async resources are closed on exit. This is only an integration milestone:
normal SSE and replay are unchanged, no general production inference
switch has been granted, and any more general service deployment needs
an independently reviewed abuse-resistance and cost-control design.
