# Automatic Azure Container Apps deployment on main

The workflow `.github/workflows/azure-container-apps-deploy.yml` verifies Python
and frontend checks, builds a linux/amd64 runtime image, pushes it to the
existing Basic Azure Container Registry, updates only the existing Container
App by immutable digest, and checks its HTTPS /health endpoint. PR builds never
receive Azure OIDC authentication. Production Foundry inference stays off.

## Identity design

Use a **dedicated Entra app registration and service principal with federated
GitHub Actions OIDC credentials**, not an interactive human account, password,
registry admin credential or client secret. Federation matches only
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

## One-time operator configuration (fish shell)

These steps make Azure directory/RBAC changes and require existing admin
permissions to create application registrations and role assignments.
Inspect each scope before running. The authorized existing resources are
subscription `98d4eb09-a320-4b90-aa9c-e561835357af`, resource group
`rg-matchpulse-dev`, Azure region `swedencentral`.

```fish
set -gx SUB 98d4eb09-a320-4b90-aa9c-e561835357af
az account set --subscription $SUB
set -gx TENANT_ID (az account show --query tenantId -o tsv)
set -gx CI_APP_ID (az ad app create --display-name matchpulse-github-actions-deploy --query appId -o tsv)
set -gx CI_APP_OBJECT_ID (az ad app show --id $CI_APP_ID --query id -o tsv)
az ad sp create --id $CI_APP_ID
```

Create the exact federated identity trust (no secrets). Use standard Bash
`printf`/JSON utilities if you prefer; the following fish command uses
`string join` to construct the JSON object:

```fish
set -l credential '{"name":"pitchvolt-main","issuer":"https://token.actions.githubusercontent.com","subject":"repo:niktolis/pitchvolt-ai:ref:refs/heads/main","description":"Only GitHub main can deploy PitchVolt","audiences":["api://AzureADTokenExchange"]}'
az ad app federated-credential create --id $CI_APP_OBJECT_ID --parameters $credential

set -gx CI_PRINCIPAL_ID (az ad sp show --id $CI_APP_ID --query id -o tsv)
set -gx ACR_ID (az acr show -n matchpulsea433a4e04d --query id -o tsv)
set -gx ACA_ID (az containerapp show -g rg-matchpulse-dev -n matchpulse-web --query id -o tsv)
az role assignment create --assignee-object-id $CI_PRINCIPAL_ID --assignee-principal-type ServicePrincipal --role AcrPush --scope $ACR_ID
az role assignment create --assignee-object-id $CI_PRINCIPAL_ID --assignee-principal-type ServicePrincipal --role Contributor --scope $ACA_ID

gh variable set AZURE_CLIENT_ID --repo niktolis/pitchvolt-ai --body $CI_APP_ID
gh variable set AZURE_TENANT_ID --repo niktolis/pitchvolt-ai --body $TENANT_ID
gh variable set AZURE_SUBSCRIPTION_ID --repo niktolis/pitchvolt-ai --body $SUB
```

`gh auth status` and `az account show` must reference the expected GitHub
and Azure accounts. **Do not paste bearer tokens or passwords.** If identity
creation fails due to Entra permissions, stop and request a directory
administrator to approve only these narrow operations; do not enable registry
admin access or create a long-lived secret as a workaround.

## Readiness and rollout

1. Merge the deployment workflow through normal PR checks. Its new `main`
   run fails closed at the identity-configuration stage until the repository
   variables are available.
2. Provision the federated identity/role assignments once and allow Azure RBAC
   propagation.
3. In Actions, manually run **Deploy Azure Container App** once using
   `workflow_dispatch` to verify authentication and image push. Thereafter,
   pushes/merges to `main` trigger deploys automatically. Avoid another
   simultaneous operator-side container update.
4. Read the action logs and verify the hosted React UI and both SSE endpoints.
   The health check verifies availability, not full product correctness.
5. Rollback by updating the existing app to the last verified immutable digest.
   Do not delete the resource group, shared Log Analytics workspace, Foundry
   resources or ACR.

**Cost boundary:** Azure budget alerts are not a guaranteed spending cap.
Each successful merge builds and pushes another image; ACR Basic storage,
network operations and Container Apps consumption may incur costs. The workflow
does not create new Azure resources or call paid Foundry inference.
