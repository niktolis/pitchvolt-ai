"""Zero-network local readiness gate for the optional Foundry live smoke.

No Azure credential, model, HTTP transport, or inference client is created.
Run this after syncing the frozen optional dependency set, and BEFORE asking
the operator to authorize exactly one billable smoke invocation.
"""
from __future__ import annotations

import argparse
import json
import os
from importlib import metadata

from pitchvolt.foundry_config import (
    NARRATIVE_ROLE_CALLS,
    SMOKE_SETTINGS,
    isolated_foundry_config,
    plausible_project_endpoint,
)
from pitchvolt.foundry_smoke import fixture

REQUIRED_DISTRIBUTIONS = (
    "agent-framework-foundry",
    "azure-identity",
    "azure-ai-projects",
)


def evaluate(endpoint: str) -> dict[str, object]:
    """Return only allowlisted metadata; never echo the project URL or secrets."""
    bundle = fixture()
    dependencies: dict[str, str | None] = {}
    for name in REQUIRED_DISTRIBUTIONS:
        try:
            dependencies[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            dependencies[name] = None

    endpoint_ok = plausible_project_endpoint(endpoint)
    if endpoint_ok:
        try:
            isolated_foundry_config(endpoint, evidence_event_count=len(bundle.events))
        except ValueError:
            endpoint_ok = False

    ready = endpoint_ok and all(value is not None for value in dependencies.values())
    return {
        "mode": "OFFLINE_PREFLIGHT",
        "status": "READY_FOR_OPERATOR_APPROVAL" if ready else "BLOCKED",
        "endpoint_is_valid_project_url": endpoint_ok,
        "endpoint_value_redacted": True,
        "endpoint_existence_verified": False,
        "model_deployments_verified": False,
        "subscription_credit_verified": False,
        "dependencies": dependencies,
        "fixture": SMOKE_SETTINGS.scenario,
        "insight_id": bundle.insight.insight_id,
        "evidence_event_count": len(bundle.insight.evidence_event_ids),
        "analyst_deployment": SMOKE_SETTINGS.analyst_deployment,
        "storyteller_deployment": SMOKE_SETTINGS.storyteller_deployment,
        "role_invocation_ceiling": NARRATIVE_ROLE_CALLS,
        "analyst_output_token_cap": SMOKE_SETTINGS.analyst_output_tokens,
        "http_max_retries": SMOKE_SETTINGS.http_max_retries,
        "role_level_retries": SMOKE_SETTINGS.role_level_retries,
        "cloud_requests_made": 0,
        "billable_inference_permitted": False,
        "warning": (
            "A successful offline check does not validate Azure authentication, "
            "quota, spending limits, model availability or any actual Agent.run "
            "response. A later live run can consume multiple model/tool rounds."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-endpoint",
        default=os.environ.get("PITCHVOLT_FOUNDRY_PROJECT_ENDPOINT", ""),
        help="Local Foundry project URL; never printed or transmitted",
    )
    args = parser.parse_args(argv)
    report = evaluate(args.project_endpoint)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "READY_FOR_OPERATOR_APPROVAL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
