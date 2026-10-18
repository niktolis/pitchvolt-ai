# GitHub repository cutover — PitchVolt AI

The new repository identity is **`niktolis/pitchvolt-ai`**, while the
existing Azure resources deliberately retain their physical, already deployed
names. **Never replace an Azure resource identifier just because the product
was rebranded.** Container Apps, ACR, resource group, managed identity and
Foundry names require separate, potentially billable infrastructure migration;
none is authorized in this change.

## Existing infrastructure (do not rename or recreate)

- Production website: https://pitchvolt.app
- Existing Container App: `matchpulse-web`
- Resource group: `rg-matchpulse-dev`
- Container Registry: `matchpulsea433a4e04d`
- Existing ACR-pull identity: `matchpulse-acr-pull`
- Existing Entra application registration: retain its current application
  (client) ID from the repository variable `AZURE_CLIENT_ID`.
- Existing Foundry resources, subscriptions, GitHub Project #6 and billing
  controls remain unchanged.

These infrastructure identifiers are immutable deployment references,
**not** new product branding.

## Zero-new-resource cutover sequence

1. Merge the consolidated code rebrand PR into the original repository.
   Confirm Python, frontend and architecture CI checks green and inspect
   the existing production deployment workflow.
2. Before renaming the GitHub repository, add a *second federated credential
   to the existing Entra app* with the immutable OIDC subject:
   `repo:niktolis@1533654/pitchvolt-ai@1419712503:ref:refs/heads/main`, issuer
   `https://token.actions.githubusercontent.com`, audience
   `api://AzureADTokenExchange`. Retain the old subject during the
   transition, so pre-rename deployments still authenticate.
3. Verify this new credential was added to the **same** Entra application.
   Do not register another app, assign new roles, change resource group,
   provision Azure resources or enable Foundry inference.
4. As repository administrator, use GitHub **Settings → General →
   Repository name → Rename** and enter **`pitchvolt-ai`**. Alternatively,
   with an authenticated GitHub CLI: `gh repo rename pitchvolt-ai --repo
   niktolis/matchpulse-ai`. This repository rename itself is an
   administrator action; it is not achievable through the currently connected
   repository-content API.
5. Verify the new canonical URL
   `https://github.com/niktolis/pitchvolt-ai`, GitHub Project #6, issue/PR
   relationships, branch protections, Actions permissions and the variables
   `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` and `AZURE_SUBSCRIPTION_ID`.
   GitHub normally redirects the old repository URL, but update local clones
   explicitly: `git remote set-url origin
   https://github.com/niktolis/pitchvolt-ai.git`.
6. Trigger/inspect **Deploy Azure Container App** only after OIDC is ready.
   It must authenticate as the pre-existing Entra app, push the `pitchvolt`
   OCI image repository to the **existing** ACR and update the **existing**
   Container App by immutable digest. Verify `https://pitchvolt.app/health`
   and the exact deployed revision. No new Foundry inference is permitted.
7. Once the renamed repository's CI/deployment identity is demonstrated,
   optionally delete the *obsolete* old federated credential (not the Entra
   application or managed identity). Keep rollback digests and source history.

## Operator-side verification (fish shell)

Use the existing GitHub repository variables; do **not** generate a new
service principal:

```fish
set -gx CI_APP_ID (gh variable get AZURE_CLIENT_ID --repo niktolis/pitchvolt-ai)
set -gx CI_APP_OBJECT_ID (az ad app show --id $CI_APP_ID --query id -o tsv)
az ad app federated-credential list --id $CI_APP_OBJECT_ID --output table
```

Add only this credential if it does not already exist:

```fish
set -l identity '{"name":"pitchvolt-main","issuer":"https://token.actions.githubusercontent.com","subject":"repo:niktolis@1533654/pitchvolt-ai@1419712503:ref:refs/heads/main","description":"PitchVolt main branch GitHub Actions","audiences":["api://AzureADTokenExchange"]}'
az ad app federated-credential create --id $CI_APP_OBJECT_ID --parameters $identity
az ad app federated-credential list --id $CI_APP_OBJECT_ID --output table
```

The credential modification affects existing Entra identity configuration;
it does not create a billable Azure compute service. It does require sufficient
identity-administrator permissions. Avoid unnecessary role assignments and
do not paste credentials or access tokens in issues or chat.

## Cutover risks and rollback

The *critical risk* is the exact immutable-subject GitHub OIDC trust. After repository
rename, the old `repo:niktolis@1533654/matchpulse-ai@1419712503:ref:refs/heads/main`
subject no longer matches GitHub's renamed identity. Without the new
federated credential, deployments fail to authenticate, although the
existing application remains hosted. Existing GitHub repository redirects
do not automatically rewrite Azure federated credentials.

The runtime environment variable has intentionally been renamed to
`PITCHVOLT_NARRATIVE_PROVIDER`; the new OCI image and backend use this
consistently. Physical resource names are left intact. Revert the GitHub
rename and/or use the last verified container-image digest if the cutover
cannot be validated; no production resources should be deleted.
