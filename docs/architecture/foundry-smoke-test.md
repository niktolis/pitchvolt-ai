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
   Set `PITCHVOLT_FOUNDRY_PROJECT_ENDPOINT` to that URL. The project endpoint is
   **not** the `.../openai/v1/` model-inference base URL shown on a deployment page.
   Role-based authorization for the signed-in identity may be required.

## Commands

```bash
uv run --frozen --extra foundry python -m pitchvolt.foundry_smoke

# Only after reviewing the dry run and verifying the endpoint/active Azure account:
uv run --frozen --extra foundry python -m pitchvolt.foundry_smoke --execute --acknowledge-billable-inference
```

Under fish shell, set the endpoint with:
```fish
set -x PITCHVOLT_FOUNDRY_PROJECT_ENDPOINT 'https://<account>.services.ai.azure.com/api/projects/<project>'
```

No secrets belong in source, CLI history, screenshots, PR comments or test reports.
The isolated smoke harness uses **`AzureCliCredential`**, which relies on `az login` and does not probe local Managed Identity endpoints. General application credentials are unchanged. A hanging Azure CLI token request or SDK network call may still need manual interruption.
Do not invoke the live command twice without separate authorization: an SDK failure,
timeout or fallback can still incur token charges, even when the report shows no usage.

### Hard boundaries and diagnostics

- Only **one** fixture insight and a fresh `FoundryRoles` instance per invocation.
- Local ceiling: one Analyst `Agent.run` and one Storyteller `Agent.run`. If the
  Analyst fails validation, the Storyteller is not invoked. No Editorial role.
- No automatic HTTP retries by this smoke harness (effective `max_retries=0`). The SDK may still perform
  additional model calls during its tool loop. **This is not an API-request or
  monetary hard cap.** Azure rate limits and credit balance should be checked separately.
- Returns nonzero unless both roles, model-initiated evidence retrieval, and final
  verified publication succeeded. Reports observable SDK token counts (if available),
  durations and evidence IDs; missing SDK usage is not proof of zero consumption.
- Do not change `PITCHVOLT_NARRATIVE_PROVIDER`, application SSE opt-in or Azure
  resource settings; the usual application path stays deterministic/offline.
- Both existing deployments have 20,000 TPM capacity (read-only Foundry discovery, 18 October 2026). TPM is not available trial credit. A 30-second per-role timeout may still be insufficient for multiple SDK tool rounds.
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

Historical note: the CLI formerly budgeted 512 Analyst output tokens. The reviewed isolated smoke uses **6144** Analyst and **1024** Storyteller output tokens; production defaults remain at 256. An earlier Analyst response exhausted a smaller token allocation; this does not establish the outcome of the next call. GPT-5 reasoning tokens may consume part of the response budget. The higher cap can increase charges or exceed a deployment's TPM allocation; do not change quotas or run inference without explicit approval. The CLI dry run displays the proposed budget without Azure requests.

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
`PITCHVOLT_FOUNDRY_PREVIEW_ENABLED=true`, a random, private
`PITCHVOLT_FOUNDRY_PREVIEW_TOKEN` (at least 32 characters), and the
existing `PITCHVOLT_FOUNDRY_PROJECT_ENDPOINT`. The HTTP request must
originate from localhost and carry `X-PitchVolt-Inference-Token` with
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
disabled, the Analyst output cap is 6144 and Storyteller cap 1024, and each role is limited
to one invocation (SDK tool rounds may still consume additional requests).
The existing deterministic verifier produces the publishable narrative;
provider failure returns evidence-backed fallback, not unverified prose.
Async resources are closed on exit. This is only an integration milestone:
normal SSE and replay are unchanged, no general production inference
switch has been granted, and any more general service deployment needs
an independently reviewed abuse-resistance and cost-control design.

## Milestone A/B readiness gate — no cloud, no credentials

**First, after checking out the reviewed PR branch**, install the frozen
optional dependency set:

```fish
git fetch origin
git switch feat/4-foundry-offline-readiness-and-local-smoke
git pull --ff-only origin feat/4-foundry-offline-readiness-and-local-smoke
uv sync --frozen --extra dev --extra foundry
uv run --frozen --extra foundry bash scripts/check.sh
uv run --frozen --extra foundry python -m pitchvolt.foundry_smoke
```

Next, obtain the actual project endpoint from **Microsoft Foundry →
your project → Overview / Project details** (confirm the field is the
project endpoint and not the resource or OpenAI inference endpoint).
Set `PITCHVOLT_FOUNDRY_PROJECT_ENDPOINT` **locally** to its exact value
(no API keys or query parameters). **Replace both YOUR-ACCOUNT and
YOUR-PROJECT below**. Copying the literal example must now return BLOCKED:

```fish
set -gx PITCHVOLT_FOUNDRY_PROJECT_ENDPOINT 'https://YOUR-ACCOUNT.services.ai.azure.com/api/projects/YOUR-PROJECT'
uv run --frozen --extra foundry python -m pitchvolt.foundry_preflight
```

The preflight now explicitly rejects template markers such as
`YOUR-ACCOUNT`, `YOUR-PROJECT`, `replace-me` and `placeholder`.
The first operator run inadvertently used the literal example and showed
READY despite no actual project URL; this was only a shape check, not
verification of a Foundry service, and is now prevented.

The preflight **never initializes Azure credentials, opens a connection or
invokes any model**. It only checks installed distributions, the locally
validated endpoint format, fictional fixture/evidence counts, and the shared
typed deployment/cost settings. The command does not print the endpoint
value, secrets, or the project name. It must say
`READY_FOR_OPERATOR_APPROVAL` and `cloud_requests_made: 0` before a
billable test is considered. Its report now explicitly sets `endpoint_existence_verified=false`,
`model_deployments_verified=false`, and
`subscription_credit_verified=false`. It does **not** validate tenant
RBAC, availability, model deployments, TPM quotas or Azure subscription
credit balance. Operator confirmation in the Azure portal is mandatory.

Operator separately checks the Azure account and cost through
`az account show` and the Azure portal. Avoid dumping access tokens.
Only **after** merging, explicit live-test authorization, and an independently
checked budget, run the already supported one-time invocation:

```fish
uv run --frozen --extra foundry python -m pitchvolt.foundry_smoke \
    --execute --acknowledge-billable-inference
```

**Stop after one result, whether PASS or FAIL.** The smoke has exactly
one explicit `Agent.run` attempt per role, a six-observation evidence
cap, an Analyst output cap of 6144 tokens, a Storyteller cap of 1024 tokens, and **zero HTTP retries**
for its SDK client; Agent Framework may still use several *billable*
model/tool rounds inside one role, and client timeouts do not guarantee
charges stop immediately. These controls **are not a hard monetary limit**.
A failure must not be auto-retried. The smoke emits only allowlisted
diagnostics, source IDs and validated decisions; do not share raw tokens,
unverified generated prose or complete access credentials. If cloud usage
accounting is unavailable, mark it *unknown* and check Azure billing.

This preparation is not a production model-enable approval. Normal
`/narratives/stream` stays deterministic and the localhost preview stays
disabled without its separate operator gate.

### Final offline review: template endpoints and diagnostics (18 October)

The common no-network project URL guard runs in **both** the preflight and
`foundry_smoke --execute`, before Azure credentials or SDK clients are created.
In addition to `YOUR-ACCOUNT/YOUR-PROJECT`, it rejects obvious `example`,
`sample`, `dummy`, `placeholder`, `youraccount/yourproject`, `replace-me`
and `insert-` template labels, nested account hosts, encoded project path
segments, and explicit ports. Passing this check still **does not establish
cloud existence**, model availability, credits, authentication or billing limits.

For safe collaboration, verifier fallback reason strings are replaced by a
fixed code, and shadow assertion findings report only their status and count,
never model-generated excerpts. Avoid `--show-unverified-prose` for shared logs.
A single Agent.run can still make multiple paid tool/model rounds: stop after
one operator-authorized invocation, even on failure.

### Existing Foundry resources and relaxed isolated-test profile (18 October 2026)

Operator Azure CLI output and the connected read-only Foundry account query
both verified the existing project endpoint
`https://matchpulse-ai-resource.services.ai.azure.com/api/projects/matchpulse-ai`.
The provisioned deployments are `matchpulse-gpt5-mini` (GPT-5 mini Global
Standard) and `matchpulse-gpt4o` (GPT-4o Standard), **20,000 TPM each**.
Do not create duplicate deployments to match PitchVolt branding.

Manager-approved smoke-only settings: 6144 Analyst output tokens, 1024
Storyteller output tokens, 30 seconds per role, 70 seconds for the localhost
preview's outer timeout. Production remains Foundry-disabled with its 256-token
default. The isolated test still uses zero HTTP/role-level retries.

The Foundry connector can inspect account deployments/quota but lists **zero
persistent agents**. Creating and calling a separate Foundry prompt agent
would not test PitchVolt's ephemeral two-role Python orchestrator, evidence
tool calls, or deterministic verifier. This assistant's compute environment
has neither the operator's Azure CLI sign-in nor a usable Azure credential.
Therefore the read-only Azure connection is **not** a successful billable
end-to-end integration smoke. Run the application's smoke only in an
authenticated operator environment; no new Azure resources are necessary.

Mac verification: 301 Python tests and 29 frontend tests passed; an ignored
192 KiB legacy bytecode directory was backed up safely. D2 source validation
passed, but macOS generated `deployment.svg` differs from tracked output.
Review the specific `git diff` after a local render rather than silently
committing platform-dependent SVG output.
