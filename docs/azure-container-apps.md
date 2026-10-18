# Azure Container Apps deployment readiness

## Scope and authorization

This page documents a **non-billable deployment preparation step**, not an Azure rollout. No Container Apps environment, Container App, registry, identity, Log Analytics workspace, DNS name, or deployment has been created by this PR. Existing Foundry resources are not changed. **Do not run an `az containerapp create` or `az containerapp up` command until the resource costs and public access are reviewed and approved.**

The existing production OCI image is `docker/backend.Dockerfile` target `runtime`. It combines the built React application with the non-root FastAPI process on port 8000. FastAPI serves static assets and same-origin REST/SSE. The app exposes `GET /health`. The initial cloud demo must keep `PITCHVOLT_NARRATIVE_PROVIDER=local`: no model calls are required to inspect match playback or controlled narratives.

## Cost and access requirements

- **Region:** choose where both Container Apps and any existing registry are permitted; proximity to Foundry is relevant only once separately approved inference is enabled.
- **Public access:** external ingress exposes a demo URL. Decide whether anonymous public access is acceptable before rollout; do not assume a public URL is authenticated.
- **Scale:** minimum replicas 0 and maximum 1 for initial cost control; scale-to-zero can cause cold starts and does not eliminate all associated resource costs.
- **Images:** immutable digest-pinned OCI image built for the Container Apps Linux architecture, stored in a registry with explicitly approved access.
- **Credentials:** no cloud model secrets or admin credentials in source, environment files committed to Git, container images or frontend assets. Prefer managed identity for registry pulls.
- **Budget:** alert thresholds alone are NOT a hard stop. Review estimated ACR, Container Apps, networking and logging costs; document a manual teardown command and assign an owner before deploying.
- **SSE:** preserve HTTP streaming and test browser reconnection/timeout after hosting; avoid assuming the ingress settings preserve every local behavior.
- **Rollback:** keep the previous tested image digest for reverting revisions, and review provisioned resources after the demo.

## Local validation

First build and smoke-check the runtime image locally as described in [development environments](development.md). Then inspect the planned values **without contacting Azure**:

```sh
export AZURE_RESOURCE_GROUP="your-approved-existing-resource-group"
export AZURE_CONTAINER_APP="pitchvolt-web"
export AZURE_CONTAINER_ENV="your-approved-environment"
export AZURE_REGION="your-approved-region"
export AZURE_IMAGE="your-registry.azurecr.io/pitchvolt@sha256:<verified-64-hex-digest>"
export AZURE_REGISTRY_SERVER="your-registry.azurecr.io"
bash scripts/aca-preflight.sh
```

The preflight rejects remote inference, mutable image tags, and non-default replica bounds. It intentionally does **not** validate real Azure subscription authorization or create resources. Its external-ingress setting describes a pending approval, not authorization to expose an endpoint.

## Future rollout gates

1. Review current Azure subscription credits and spending controls; approve a monthly upper bound and exact resource inventory.
2. Approve public-versus-private access, registry identity, region and resource names.
3. Build and push the runtime image, record its immutable digest, and perform a clean dependency/vulnerability check.
4. Provision the minimal Container Apps environment and app using reviewed infrastructure-as-code, with remote inference disabled.
5. Inspect health, frontend assets, match-event SSE, narrative SSE, diagnostics and rollback/teardown. Measure browser latency before considering any hosted Foundry inference.

## Operator rollout playbook

After selecting a verified subscription, region, resource group, registry name, environment name and app name, set their corresponding `AZURE_*` environment variables and run `bash scripts/aca-rollout-plan.sh`. The script **prints** an ordered Azure CLI procedure, without executing any Azure mutations. This is necessary because the current Foundry integration cannot provision Container Apps, and because public ingress and cloud costs require operator review. The script deliberately stops short of generating a ready-to-run Container App creation command until a digest-pinned image and managed-identity registry-pull RBAC are verified. Use an existing resource group only, and inspect current resources before adding or deleting any. Confirm the credit balance and cost exposure before each chargeable step.
