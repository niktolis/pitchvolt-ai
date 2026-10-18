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
  receive Owner, subscription Contributor, directory admin or Foundry access.

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
network operations and Container Apps consumption may incur costs. The workflow
does not create new Azure resources or call paid Foundry inference.
