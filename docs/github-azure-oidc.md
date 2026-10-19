# Automatic Azure Container Apps deployment on main

The workflow `.github/workflows/azure-container-apps-deploy.yml` verifies Python
and frontend checks, builds a linux/amd64 runtime image, pushes it to the
existing Basic Azure Container Registry, updates only the existing Container
App by immutable digest, and checks its HTTPS /health endpoint. PR builds never
receive Azure OIDC authentication. Production Foundry inference stays off.

## Identity design

Use a **dedicated Entra app registration and service principal with federated
GitHub Actions OIDC credentials**, not an interactive human account, password,
registry admin credential or client secret. The production deployment and merged-PR workflows use **separate OIDC
subjects** and audience `api://AzureADTokenExchange`. Both authenticated
jobs request `id-token: write`. The separate existing user-assigned managed
identity `matchpulse-acr-pull` continues to serve private ACR image pulls at
Container Apps runtime; do not remove or reuse it for CI.

The deployment identity requires only:
- `AcrPush` on registry `matchpulsea433a4e04d`.
- `Contributor` on **only** the existing container app `matchpulse-web`
  (replace with a narrower tested deployment role if supported). It must not
  receive Owner, subscription Contributor or directory admin. Foundry inference
  requires a separate, project-scoped **Foundry User** assignment on the existing
  `matchpulse-ai` project, only for the merged-PR smoke described below.

## Existing Azure identity — repository rename

The production deployment already uses an approved Entra application with
GitHub Actions OIDC. **Reuse it**: do not create an application registration,
service principal, Azure resource, managed identity or new RBAC assignment.
The existing GitHub variables `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and
`AZURE_SUBSCRIPTION_ID` are retained by the GitHub repository rename.

The new canonical GitHub repository is `niktolis/pitchvolt-ai`. A
repository-name change changes the OIDC token's exact `sub` claim, so an
additional federated credential for that name must be configured on the
**existing** Entra application **before** the rename. Keep the old subject
during cutover and remove it only after confirming the new identity works.
No Foundry model invocation or paid resource provisioning is involved.

See [repository-name migration runbook](repository-rename.md) for the exact
operator sequence, fish commands, physical Azure resource identifiers,
rollback and verification.

## Readiness and rollout

1. Verify the existing `main` workflow remains operational on the
   original repository after the code refactor.
2. Add only the new exact-subject federated credential on the existing Entra
   app, then rename the GitHub repository as documented in the runbook.
3. Inspect repository variables and the new OIDC identity. Verify the normal
   **Deploy Azure Container App** workflow after cutover; do not deploy
   concurrently from another operator session.
4. Read the action logs and verify the hosted React UI and both SSE endpoints.
   The health check verifies availability, not full product correctness.
5. Rollback by updating the existing app to the last verified immutable digest.
   Do not delete the resource group, shared Log Analytics workspace, Foundry
   resources or ACR.

**Cost boundary:** Azure budget alerts are not a guaranteed spending cap.
Each successful merge builds and pushes another image; ACR Basic storage,
network operations and Container Apps consumption may incur costs. The production deployment workflow does not create new Azure resources or call
paid Foundry inference. A **separate merge-only smoke workflow** now invokes
the already-deployed models after approved PR merges.

## One-time Foundry CI authorization and merged-PR event

The independent `.github/workflows/foundry-merge-smoke.yml` uses
`pull_request_target` **only** on PR closure to `main`, runs its job **only**
for `merged=true`, and checks out the trusted **merge commit**, never the
unmerged PR head. This event uses the verified immutable `:pull_request` subject below,
not the main-branch deployment subject.
It requests `id-token: write` only in this job and reuses
`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.
There are **no push/synchronize/schedule/manual-dispatch triggers**.
Automatic retries and rerun attempts are suppressed.

The user verified on 19 October 2026 that the existing CI service principal
has **Reader** on the Foundry account and **Foundry User** on the project.
No additional IAM assignment is required unless permissions change. Project
resource scope:
`/subscriptions/98d4eb09-a320-4b90-aa9c-e561835357af/resourceGroups/rg-matchpulse-dev/providers/Microsoft.CognitiveServices/accounts/matchpulse-ai-resource/projects/matchpulse-ai`.

Read-only audit (do not create duplicate role assignments):
```bash
CI_PRINCIPAL_OBJECT_ID="$(az ad sp show --id "$AZURE_CLIENT_ID" --query id -o tsv)"
az role assignment list --assignee "$CI_PRINCIPAL_OBJECT_ID" \
  --scope "/subscriptions/98d4eb09-a320-4b90-aa9c-e561835357af/resourceGroups/rg-matchpulse-dev/providers/Microsoft.CognitiveServices/accounts/matchpulse-ai-resource/projects/matchpulse-ai" \
  --include-inherited --query '[].{role:roleDefinitionName,scope:scope}' -o table
```

Avoid granting Owner, Contributor, Key Vault access, key-based inference or
additional model-deployment privileges. If the project-scoped role is
incompatible with the account's inference API, inspect the actual 403 and
Foundry RBAC documentation; do not silently assign broad subscription roles.
This one-time IAM configuration is already complete.

The workflow generates a sanitized CI Job Summary and 7-day JSON artifact
with factual evidence IDs, typed role decisions, timings, verifier status and
optional token usage. Any failure remains failed without an automated retry.
The existing free-trial spending limit is the Azure-side financial boundary;
GitHub action settings/TPM do not hard-stop spending at a specified amount.

[Automatic merge smoke runbook](architecture/foundry-smoke-test.md).

## Verified GitHub OIDC federation and first authenticated run

The Entra CI app (client ID `ac059fd4-4f84-43ca-ab1f-ff0ac3d4aa51`) now
has **both** credentials with issuer `https://token.actions.githubusercontent.com`
and audience `api://AzureADTokenExchange`:

| Credential | Exact observed OIDC subject |
|---|---|
| `pitchvolt-main` | `repo:niktolis@1533654/pitchvolt-ai@1419712503:ref:refs/heads/main` |
| `pitchvolt-foundry-pr-merge` | `repo:niktolis@1533654/pitchvolt-ai@1419712503:pull_request` |

Do not remove the branch credential to configure the pull-request
credential. Initial PR #130 merge returned `AADSTS700213` for the
missing second subject before inference. The PR #135 merge
[automated workflow](https://github.com/niktolis/pitchvolt-ai/actions/runs/39211398821)
subsequently **authenticated**, validated deployments, and executed
both model roles plus the controlled verifier. It ended **FAIL** only
because smoke acceptance incorrectly required optional shadow prose
that was not returned. No generated text was published, and model
token usage was unavailable. The acceptance fix does not change IAM
or authorize retries.
