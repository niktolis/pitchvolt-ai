#!/usr/bin/env bash
# Produce reviewed CLI commands; never executes Azure mutations.
set -euo pipefail
: "${AZURE_SUBSCRIPTION_ID:?Set target subscription ID}"
: "${AZURE_RESOURCE_GROUP:?Set approved resource group}"
: "${AZURE_REGION:?Set approved region}"
: "${AZURE_REGISTRY_NAME:?Set globally unique registry name}"
: "${AZURE_CONTAINER_ENV:?Set environment name}"
: "${AZURE_CONTAINER_APP:?Set app name}"
if [[ "${MATCHPULSE_NARRATIVE_PROVIDER:-local}" != "local" ]]; then
  echo "Refusing Foundry-enabled demo plan" >&2
  exit 1
fi

cat <<'NOTICE'
This script PRINTS a deployment playbook; it DOES NOT execute Azure changes.
Container Registry Basic, Container Apps environment, builds and logging can
incur charges. Azure budget alerts do NOT stop spending. No hard cap is provided.
Review subscription balance, service prices, resource names, public access, and
teardown before running any generated command. No Foundry inference is enabled.
NOTICE

printf '\nSubscription: %s\nRegion: %s\nResource group: %s\n' \
  "$AZURE_SUBSCRIPTION_ID" "$AZURE_REGION" "$AZURE_RESOURCE_GROUP"

cat <<'STEPS'

# 1) Set subscription; inspect existing resources before creating new ones.
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
az group show --name "$AZURE_RESOURCE_GROUP"
az resource list --resource-group "$AZURE_RESOURCE_GROUP" --output table

# 2) AFTER cost approval, create Basic registry if it does not exist.
az acr create --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$AZURE_REGISTRY_NAME" --sku Basic --admin-enabled false

# 3) Build existing production image in Azure (can incur build charges).
az acr build --registry "$AZURE_REGISTRY_NAME" \
  --image "matchpulse:demo" --file docker/backend.Dockerfile \
  --target runtime .

# 4) Resolve the immutable manifest digest from registry results before deploy:
az acr manifest list-metadata --registry "$AZURE_REGISTRY_NAME" \
  --name matchpulse --output table

# 5) Create minimal Container Apps environment (may create logs/monitoring).
az containerapp env create --resource-group "$AZURE_RESOURCE_GROUP" \
  --name "$AZURE_CONTAINER_ENV" --location "$AZURE_REGION"

# 6) Create a managed identity and allow ACR image pull (requires AcrPull).
#    Review RBAC propagation, then create app with digest-pinned image:
#    <registry>.azurecr.io/matchpulse@sha256:<verified-digest>
#    target-port=8000, ingress=external, min-replicas=0, max-replicas=1.
#    MATCHPULSE_NARRATIVE_PROVIDER=local (never enable Foundry in this rollout).
#    The final create command is intentionally not auto-generated until
#    registry identity and actual digest have been verified.

# 7) Verify GET /health, UI, event SSE, narrative SSE and fallback in browser.
# 8) Deprovision after the demo: containerapp delete, env delete, acr delete.
#    Confirm deletion and remaining Azure resource list.
STEPS
