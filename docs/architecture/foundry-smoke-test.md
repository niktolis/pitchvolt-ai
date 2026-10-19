# Foundry: automatic live smoke after a merged pull request

**Current policy (19 October 2026, issue #4, PR #130):** once a PR has been
reviewed and **merged into `main`**, GitHub Actions runs one billable
PitchVolt Analyst → Storyteller → deterministic Verifier experiment.
This is a standing authorization for this specific bounded experiment on
qualifying merges. Do not ask the operator to execute inference on macOS,
and do not request separate approval for each merge-triggered smoke.
**Do not merge PRs without manager approval.**

Workflow: `.github/workflows/foundry-merge-smoke.yml`.

## Event contract

- Trigger: **`pull_request_target` with `types: [closed]` and `branches:
  [main]`**. Its sole job requires `merged == true`, the expected base
  repository and `github.run_attempt == 1`.
- **No `push`, `pull_request:synchronize`, `workflow_dispatch` or cron
  trigger.** Pushes, PR updates, and unmerged closures never make billable
  inference requests. An Actions run may appear as skipped for an unmerged PR.
- Check out the exact `merge_commit_sha` after merging and verify it is in
  trusted `origin/main` history. Never execute PR-head code with OIDC.
  The `pull_request_target` default-branch OIDC subject is reused from the
  existing production GitHub federation.
- Runner: GitHub-hosted Ubuntu 24.04 / Python 3.12; `uv --frozen` optional
  Foundry dependency graph; no custom image, hosted agent, or new resource.
- Offline URL/SDK preflight, followed by OIDC login, subscription/deployment
  checks, and **one** `python -m pitchvolt.foundry_smoke --execute
  --acknowledge-billable-inference --report-file ...` invocation.
- Failure is nonzero and uploads a sanitized diagnostic artifact if one was
  produced. No scripted HTTP retries, role-level retries, or automated
  follow-up runs. Developer-facing `--show-unverified-prose` is forbidden
  together with `--report-file`.
- Logs and `GITHUB_STEP_SUMMARY` show a bounded evidence/role/latency/token
  status. `actions/upload-artifact@v4` retains the sanitized JSON report
  for **7 days**. An early OIDC or preflight failure has no model report.

**The first merge containing the new workflow may not always receive its
own `pull_request_target` run**, because GitHub resolves workflow definitions
from the default branch as events arrive. Verify the workflow exists on
`main` after PR #130 merges. Subsequent qualifying merges use it
automatically; don't add a push/dispatch trigger as a workaround without
reviewing the one-run-per-merge requirement.

## Azure identity: one-time setup, not per-merge approval

Existing project endpoint:
`https://matchpulse-ai-resource.services.ai.azure.com/api/projects/matchpulse-ai`.

Existing deployment | Model | Azure capacity
---|---|---
`matchpulse-gpt5-mini` | GPT-5 mini, Global Standard | 20,000 TPM
`matchpulse-gpt4o` | GPT-4o, Standard | 20,000 TPM

The repository already defines `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`,
`AZURE_SUBSCRIPTION_ID` for `azure/login@v3` on `main`. Reuse its federated
credential subject `repo:niktolis/pitchvolt-ai:ref:refs/heads/main` and
audience `api://AzureADTokenExchange`. The client ID belongs to the
existing CI Entra app, **not** the operator's workstation login.

**One-time RBAC verification may be necessary:** production deployment
permissions do not imply Microsoft Foundry inference permission.
Authorize the existing CI Entra service principal with **Foundry User**
(previously Azure AI User) on the **existing Foundry project scope**, with
account-level scope only if the project-scoped grant proves insufficient.
An Azure administrator must perform this assignment if it does not
exist. This is an IAM configuration step, *not* a model invocation and
not an approval needed per merge. Do not give the CI identity Owner,
subscription Contributor, model management or key access for this job.
See [GitHub/Azure OIDC runbook](../github-azure-oidc.md).

Only the existing trial subscription
`98d4eb09-a320-4b90-aa9c-e561835357af` is accepted. Its spending
limit must remain enabled. Azure budget alerts do not stop expenditure;
no GitHub Actions job provides a financial hard cap. Each triggered
smoke potentially incurs several Azure model/tool rounds. The 20,000 TPM
quotas are *not* remaining credit. The workflow does not provision,
modify or delete Azure resources.

## What the CI smoke proves

The fixed `high_press` canonical fixture exercises **six** evidence
events. Real `FoundryRoles` instances invoke the existing ephemeral
Analyst and Storyteller with Pydantic typed outputs. The deterministic
verifier requires complete evidence, canonical four-slot ordering and
strict source-backed narrative facts. Invalid plans, missing events,
incomplete ordering, transport errors and provider timeouts cause a
**non-successful live smoke** even if a safe deterministic fallback is
returned. Original Storyteller prose stays shadow-only; arbitrary
model-authored text is not declared semantically verified or published.

Smoke-specific settings are 6144 Analyst output tokens, 1024
Storyteller output tokens, up to 30 seconds per role, maximum one
`Agent.run` attempt per role, **zero OpenAI SDK HTTP retries**.
Agent Framework tool rounds may still issue more than two model calls.
The production public `/narratives/stream` remains locally controlled,
with Foundry inference disabled and the original 256-token defaults.

A passing run should report `source=controlled`, **6/6** observed evidence
tools, exactly two specialist roles, a publish action, a shadow-only
candidate, and a zero exit code. The sanitized JSON artifact includes
structured role decisions, evidence identifiers, role latency, verifier
status, and supported token usage if available. Null token usage means
**unknown**, never zero cost. A failure requires analysis of the **existing
run artifact**, not an unattended retry.

## Recorded real application evidence (18 October 2026)

An authenticated macOS smoke (on the PR branch) already **passed**:
6/6 read-only evidence event tool calls, Analyst 14.93 s, Storyteller
3.84 s, fully structured Analyst/Storyteller selections and complete
`fact_order=[team,tactic,transition,actions]`; verifier action
`publish` and `source=controlled`. Original prose failed the bounded
grammar eligibility and was deliberately **not** published.
SDK `input_tokens`/`output_tokens` were null, not zero. This
establishes live integration for **one** synthetic fixture. It does
not establish general editorial semantic safety or production
Foundry enablement.

Historical troubleshooting: prior runs saw Managed Identity credential
probing, a sync/async Azure SDK client mismatch, token-budget length
truncation, and incomplete `fact_order`. The current test uses
`AzureCliCredential` (which works with `azure/login` on GitHub Actions),
async `AIProjectClient`, `max_retries=0`, higher isolated budgets,
and exact typed validation. Future deviations must be diagnosed from the
merge CI artifact before code changes are proposed.

## Debugging

Find the **Foundry smoke on merged PR** workflow on the repository
Actions page, open its `foundry-live-smoke` job, then read the
`GITHUB_STEP_SUMMARY` and download the `foundry-merge-pr-...` artifact.
If the OIDC login fails, inspect the federation subject/main binding;
if model requests return 401/403, check the project's Foundry User
assignment for the GitHub CI service principal. A failure before Python
starts cannot have an inference report. The normal pre-merge Python,
frontend, D2 and container checks are separate from this billable
post-merge smoke, so failed Foundry tests cannot be fixed by changing
a pre-merge source branch after its merge.

For exceptional manual debugging, the same `foundry_smoke` CLI retains
its explicit flags, but the operational default is automated
merge-only CI. Do not add local commands to mandatory handovers.
