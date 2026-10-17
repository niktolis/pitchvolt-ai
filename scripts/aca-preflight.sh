#!/usr/bin/env bash
# Non-billable validation of an Azure Container Apps deployment plan.
set -euo pipefail

: "${AZURE_RESOURCE_GROUP:?Set the EXISTING approved resource group name}"
: "${AZURE_CONTAINER_APP:?Set the proposed app name}"
: "${AZURE_CONTAINER_ENV:?Set the proposed Container Apps environment}"
: "${AZURE_REGION:?Set the approved Azure region}"
: "${AZURE_IMAGE:?Set an immutable, prebuilt OCI image reference}"
: "${AZURE_REGISTRY_SERVER:?Set the approved container registry hostname}"

if [[ "${MATCHPULSE_NARRATIVE_PROVIDER:-local}" != "local" ]]; then
  echo "Refusing deployment with remote inference enabled" >&2
  exit 1
fi
if [[ "${AZURE_IMAGE}" != *@sha256:* ]]; then
  echo "Refusing mutable OCI image tag; require digest-pinned image" >&2
  exit 1
fi
if [[ "${AZURE_MIN_REPLICAS:-0}" != "0" || "${AZURE_MAX_REPLICAS:-1}" != "1" ]]; then
  echo "Preflight requires min replicas=0, max replicas=1" >&2
  exit 1
fi
if [[ "${AZURE_INGRESS:-external}" != "external" ]]; then
  echo "This plan expects the separately approved public demo access decision" >&2
  exit 1
fi

cat <<PLAN
DRY_RUN: no Azure resources created or modified
Resource group: ${AZURE_RESOURCE_GROUP}
Container App: ${AZURE_CONTAINER_APP}
Environment: ${AZURE_CONTAINER_ENV}
Region: ${AZURE_REGION}
Image: ${AZURE_IMAGE}
Registry: ${AZURE_REGISTRY_SERVER}
Ingress: external (public exposure requires explicit approval)
Target port: 8000
Health probe: /health
Min replicas: 0
Max replicas: 1
Provider: local (Foundry inference disabled)
PLAN
