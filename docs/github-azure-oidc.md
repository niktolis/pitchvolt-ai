# Automatic Azure Container Apps deployment on main

The workflow `.github/workflows/azure-container-apps-deploy.yml` verifies Python
and frontend checks, builds a linux/amd64 runtime image, pushes it to the
existing Basic Azure Container Registry, updates only the existing Container
App by immutable digest, and checks its HTTPS /health endpoint. PR builds never
receive Azure OIDC authentication. Production Foundry inference stays off.

## Identity design

Use a **dedicated Entra app registration and service principal with federated
GitHub Actions OIDC credentials**, not an interactive human account, password,
registry admin credential or client secret. After the repository rename, federation must match
`repo:niktolis/pitchvolt-ai:ref:refs/heads/main` and audience
`api://AzureADTokenExchange`. The GitHub job requests `id-token: write`
only for the deployment job. The separate existing user-assigned managed
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
unmerged PR head. GitHub's post-2025 default-branch context preserves
the existing subject `repo:niktolis/pitchvolt-ai:ref:refs/heads/main`.
It requests `id-token: write` only in this job and reuses
`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.
There are **no push/synchronize/schedule/manual-dispatch triggers**.
Automatic retries and rerun attempts are suppressed.

The existing deployment service principal has no documented Foundry data-plane
grant. An Azure IAM administrator must **once** assign **Foundry User**
(formerly Azure AI User) at the existing Foundry project scope to that
service principal if the assignment does not already exist. Project
resource scope:
`/subscriptions/98d4eb09-a320-4b90-aa9c-e561835357af/resourceGroups/rg-matchpulse-dev/providers/Microsoft.CognitiveServices/accounts/matchpulse-ai-resource/projects/matchpulse-ai`.

Example, for an administrator authorized to manage IAM (review scope first):
```bash
CI_PRINCIPAL_OBJECT_ID="$(az ad sp show --id "$AZURE_CLIENT_ID" --query id -o tsv)"
az role assignment create --assignee-object-id "$CI_PRINCIPAL_OBJECT_ID" \
  --assignee-principal-type ServicePrincipal --role "Foundry User" \
  --scope "/subscriptions/98d4eb09-a320-4b90-aa9c-e561835357af/resourceGroups/rg-matchpulse-dev/providers/Microsoft.CognitiveServices/accounts/matchpulse-ai-resource/projects/matchpulse-ai"
```

Avoid granting Owner, Contributor, Key Vault access, key-based inference or
additional model-deployment privileges. If the project-scoped role is
incompatible with the account's inference API, inspect the actual 403 and
Foundry RBAC documentation; do not silently assign broad subscription roles.
This step is **one-time IAM configuration**, not a merge-by-merge approval.

The workflow generates a sanitized CI Job Summary and 7-day JSON artifact
with factual evidence IDs, typed role decisions, timings, verifier status and
optional token usage. Any failure remains failed without an automated retry.
The existing free-trial spending limit is the Azure-side financial boundary;
GitHub action settings/TPM do not hard-stop spending at a specified amount.

[Automatic merge smoke runbook](architecture/foundry-smoke-test.md).
