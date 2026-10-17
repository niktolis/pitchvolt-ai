"""Explicitly authorized, one-insight Foundry smoke test; not an application toggle."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import asdict

from matchpulse.foundry_adapter import FoundryConfig, FoundryRoles, RoleSettings
from matchpulse.narrative import Audience, InMemoryEvidenceTool
from matchpulse.narrative_stream import _bundles
from matchpulse.scenarios import scenario
from matchpulse.workflow import Orchestrator

ANALYST_DEPLOYMENT = "matchpulse-gpt5-mini"
STORYTELLER_DEPLOYMENT = "matchpulse-gpt4o"
SMOKE_ANALYST_OUTPUT_TOKENS = 512


def sanitized_failure(exc: Exception) -> dict[str, object]:
    """Report only allowlisted structured metadata, never provider message bodies."""
    status = None
    code = None
    for current in (exc, exc.__cause__, exc.__context__):
        if current is None:
            continue
        value = getattr(current, "status_code", None)
        if isinstance(value, int) and 100 <= value <= 599:
            status = value
        value = getattr(current, "code", None)
        if isinstance(value, str) and value in {
            "authentication_error", "permission_denied", "rate_limit_exceeded",
            "model_not_found", "invalid_request_error", "insufficient_quota",
        }:
            code = value
        if status is not None and code is not None:
            break
    return {
        "exception_type": type(exc).__name__,
        "cause_type": type(exc.__cause__).__name__ if exc.__cause__ else None,
        "http_status": status,
        "safe_error_code": code,
        "note": "No exception message, request body, headers, or credentials printed",
    }


def fixture():
    """Pick exactly one deterministic synthetic insight, independent of Azure."""
    match, events = scenario("high_press")
    bundles = _bundles(match, events)
    if not bundles:
        raise RuntimeError("Smoke fixture did not produce a tactical insight")
    return next(iter(bundles.values()))


def arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Allow billable inference")
    parser.add_argument(
        "--acknowledge-billable-inference",
        action="store_true",
        help="Confirm the approved one-Analyst/one-Storyteller budget",
    )
    parser.add_argument(
        "--project-endpoint",
        default=os.getenv("MATCHPULSE_FOUNDRY_PROJECT_ENDPOINT", ""),
        help="Exact Foundry project endpoint (do not enter any API key)",
    )
    return parser.parse_args(argv)


async def run(argv: list[str] | None = None) -> int:
    args = arguments(argv)
    bundle = fixture()
    description = {
        "mode": "LIVE" if args.execute else "DRY_RUN",
        "scenario": "high_press",
        "insight_id": bundle.insight.insight_id,
        "evidence_event_ids": list(bundle.insight.evidence_event_ids),
        "analyst_deployment": ANALYST_DEPLOYMENT,
        "storyteller_deployment": STORYTELLER_DEPLOYMENT,
        "maximum_role_invocations": 2,
        "http_max_retries": 0,
        "analyst_max_output_tokens": SMOKE_ANALYST_OUTPUT_TOKENS,
        "note": "Agent SDK can make additional HTTP requests internally; no hard monetary cap",
    }
    print(json.dumps(description, indent=2))
    if not args.execute:
        print("No Azure credentials loaded and no inference invoked.")
        return 0
    if not args.acknowledge_billable_inference:
        raise SystemExit("Refusing live inference: add --acknowledge-billable-inference")
    config = FoundryConfig(
        project_endpoint=args.project_endpoint,
        model_deployment=ANALYST_DEPLOYMENT,
        storyteller_model_deployment=STORYTELLER_DEPLOYMENT,
        inference_explicitly_approved=True,  # isolated CLI ONLY, never SSE application
        max_tool_calls_per_analyst=min(12, len(bundle.events)),
        timeout_seconds_per_role=15.0,
        analyst_settings=RoleSettings(max_output_tokens=SMOKE_ANALYST_OUTPUT_TOKENS),
    )
    # Workstation-specific credential avoids Managed Identity probing on macOS.
    # No token or credential content is logged or stored.
    from azure.ai.projects import AIProjectClient
    from azure.identity import AzureCliCredential

    class NoRetryProjectClient(AIProjectClient):
        """Apply zero OpenAI transport retries to the manual smoke test only."""

        def get_openai_client(self, *, agent_name=None, **kwargs):
            kwargs["max_retries"] = 0
            return super().get_openai_client(agent_name=agent_name, **kwargs)

    print('AUTH: using Azure CLI credential for isolated smoke test', flush=True)
    credential = AzureCliCredential()
    project_client = NoRetryProjectClient(endpoint=config.project_endpoint, credential=credential)
    roles = FoundryRoles(config, credential=credential, project_client=project_client)
    print('ANALYST: starting first approved role invocation', flush=True)
    tool = InMemoryEvidenceTool(lambda insight_id: bundle)
    orchestrator = Orchestrator(tool, roles, roles)
    try:
        result = await orchestrator.narrate(bundle.insight.insight_id, Audience.ANALYST)
        print('RESULT: role orchestration returned', flush=True)
        report = {
            "source": result.source,
            "rejection_reason": result.rejection_reason,
            "model_initiated_evidence_tool_calls": list(roles.last_evidence_tool_calls),
            "expected_evidence_event_ids": list(bundle.insight.evidence_event_ids),
            "invocations": [asdict(item) for item in roles.invocations],
            "last_model_response_metadata": roles.last_response_metadata,
            "trace": [asdict(item) for item in result.trace],
            "verified_narrative": result.narrative.model_dump(mode="json"),
        }
        print(json.dumps(report, indent=2))
        valid = result.source == "controlled" and set(
            roles.last_evidence_tool_calls
        ) == set(bundle.insight.evidence_event_ids) and len(roles.invocations) == 2
        if not valid:
            print("FAIL: structured tool-enabled narrative not confirmed")
            return 1
        print("PASS: evidence tool, both specialist roles and verifier completed")
        return 0
    except Exception as exc:  # noqa: BLE001 - sanitize arbitrary provider/SDK failures
        # Do not print exception messages: authentication/HTTP exceptions may contain secrets.
        print("FAIL: " + json.dumps(sanitized_failure(exc), sort_keys=True))
        return 1


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
