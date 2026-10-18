"""Explicitly authorized, one-insight Foundry smoke test; not an application toggle."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import asdict

from pitchvolt.foundry_adapter import FoundryRoles
from pitchvolt.foundry_config import NARRATIVE_ROLE_CALLS, SMOKE_SETTINGS, isolated_foundry_config
from pitchvolt.intelligence import InsightKind
from pitchvolt.narrative import Audience, InMemoryEvidenceTool
from pitchvolt.narrative_stream import _bundles
from pitchvolt.scenarios import SCENARIO_NAMES, scenario
from pitchvolt.workflow import Orchestrator


def create_smoke_project_client(endpoint: str, credential: object):
    """Disable transparent HTTP retries in the one-shot billable smoke."""
    from azure.ai.projects.aio import AIProjectClient

    class ConfiguredRetryAsyncProjectClient(AIProjectClient):
        def get_openai_client(self, *, agent_name=None, **kwargs):
            kwargs["max_retries"] = SMOKE_SETTINGS.http_max_retries
            return super().get_openai_client(agent_name=agent_name, **kwargs)

    return ConfiguredRetryAsyncProjectClient(endpoint=endpoint, credential=credential)


def _validation_diagnostics(exc: Exception) -> list[dict[str, object]]:
    """Only allowlisted Pydantic error codes and schema paths, never input values."""
    output: list[dict[str, object]] = []
    for current in (exc, exc.__cause__, exc.__context__):
        if current is None or not callable(getattr(current, "errors", None)):
            continue
        try:
            errors = current.errors(include_input=False, include_url=False)
        except (TypeError, ValueError):
            continue
        if not isinstance(errors, list):
            continue
        for error in errors[:8]:
            if not isinstance(error, dict):
                continue
            kind = error.get("type")
            location = error.get("loc")
            if not isinstance(kind, str) or not kind.replace("_", "").isalnum():
                continue
            if not isinstance(location, (list, tuple)):
                location = ()
            # Do not serialize arbitrary field names: nested paths may contain user data.
            output.append({
                "type": kind[:60],
                "location_depth": min(len(location), 20),
            })
        if output:
            break
    return output


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
        "validation_diagnostics": _validation_diagnostics(exc),
        "note": "No exception message, request body, headers, or credentials printed",
    }


def fixture(name: str | None = None):
    """Pick exactly one deterministic synthetic insight, independent of Azure."""
    selected = name if name is not None else SMOKE_SETTINGS.scenario
    match, events = scenario(selected)
    bundles = _bundles(match, events)
    if not bundles:
        raise RuntimeError("Smoke fixture did not produce a tactical insight")
    return next(
        (item for item in bundles.values() if item.insight.kind == InsightKind.HIGH_PRESS),
        next(iter(bundles.values())),
    )


def arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Allow billable inference")
    parser.add_argument(
        "--scenario", default=SMOKE_SETTINGS.scenario, choices=SCENARIO_NAMES,
        help="Synthetic fixture to preflight; no inference by default",
    )
    parser.add_argument(
        "--show-unverified-prose", action="store_true",
        help="Display model-generated SHADOW-ONLY prose locally (never publish it)",
    )
    parser.add_argument(
        "--acknowledge-billable-inference",
        action="store_true",
        help="Confirm the approved one-Analyst/one-Storyteller budget",
    )
    parser.add_argument(
        "--project-endpoint",
        default=os.getenv("PITCHVOLT_FOUNDRY_PROJECT_ENDPOINT", ""),
        help="Exact Foundry project endpoint (do not enter any API key)",
    )
    return parser.parse_args(argv)


async def run(argv: list[str] | None = None) -> int:
    args = arguments(argv)
    bundle = fixture(args.scenario)
    description = {
        "mode": "LIVE" if args.execute else "DRY_RUN",
        "scenario": args.scenario,
        "insight_id": bundle.insight.insight_id,
        "evidence_event_ids": list(bundle.insight.evidence_event_ids),
        "analyst_deployment": SMOKE_SETTINGS.analyst_deployment,
        "storyteller_deployment": SMOKE_SETTINGS.storyteller_deployment,
        "maximum_role_invocations": NARRATIVE_ROLE_CALLS,
        "http_max_retries": SMOKE_SETTINGS.http_max_retries,
        "role_level_retries": SMOKE_SETTINGS.role_level_retries,
        "analyst_max_output_tokens": SMOKE_SETTINGS.analyst_output_tokens,
        "shadow_model_prose_requested": True,
        "unverified_text_display_enabled": args.show_unverified_prose,
        "note": "No SDK HTTP or role-level retries in this smoke; tool rounds may still generate multiple billable requests. This is NOT a monetary hard stop.",
    }
    print(json.dumps(description, indent=2))
    if not args.execute:
        print("No Azure credentials loaded and no inference invoked.")
        return 0
    if not args.acknowledge_billable_inference:
        raise SystemExit("Refusing live inference: add --acknowledge-billable-inference")
    config = isolated_foundry_config(
        args.project_endpoint, evidence_event_count=len(bundle.events), inference_approved=True
    )
    # Workstation-specific credential avoids Managed Identity probing on macOS.
    # No token or credential content is logged or stored.
    from azure.identity.aio import AzureCliCredential

    print('AUTH: using Azure CLI credential for isolated smoke test', flush=True)
    credential = AzureCliCredential()
    project_client = create_smoke_project_client(config.project_endpoint, credential)
    roles = FoundryRoles(config, credential=credential, project_client=project_client)
    # Both async Azure resources are closed below, including on a failed model request.
    try:
        print('ANALYST: starting first approved role invocation', flush=True)
        tool = InMemoryEvidenceTool(lambda insight_id: bundle)
        orchestrator = Orchestrator(tool, roles, roles)
        try:
            result = await orchestrator.narrate(bundle.insight.insight_id, Audience(SMOKE_SETTINGS.audience))
            print('RESULT: role orchestration returned', flush=True)
            report = {
                "source": result.source,
                "rejection_reason": result.rejection_reason,
                "model_initiated_evidence_tool_calls": list(roles.last_evidence_tool_calls),
                "expected_evidence_event_ids": list(bundle.insight.evidence_event_ids),
                "invocations": [asdict(item) for item in roles.invocations],
                "last_model_response_metadata": roles.last_response_metadata,
                "role_response_metadata": roles.role_response_metadata,
                "validated_role_decisions": roles.role_decisions,
                "bounded_grounding": (
                    asdict(roles.last_grounding_result)
                    if roles.last_grounding_result is not None else None
                ),
                "assertion_audit": (
                    asdict(roles.last_assertion_audit)
                    if roles.last_assertion_audit is not None else None
                ),
                "evidence_link_assessment": (
                    asdict(roles.last_link_assessment)
                    if roles.last_link_assessment is not None else None
                ),
                "shadow_assessment": (
                    roles.last_shadow_assessment.model_dump(mode="json")
                    if roles.last_shadow_assessment is not None else None
                ),
                "model_authored_shadow": (
                    {
                        "headline": roles.last_authored_candidate.headline,
                        "text": roles.last_authored_candidate.text,
                        "warning": "UNVERIFIED: not published or semantically certified",
                    }
                    if args.show_unverified_prose and roles.last_authored_candidate is not None
                    else None
                ),
                "token_usage_status": (
                    "complete"
                    if len(roles.invocations) == 2
                    and all(inv.input_tokens is not None and inv.output_tokens is not None
                            for inv in roles.invocations)
                    else "unavailable_or_partial"
                ),
                "trace": [asdict(item) for item in result.trace],
                "verified_narrative": result.narrative.model_dump(mode="json"),
            }
            print(json.dumps(report, indent=2))
            valid = result.source == "controlled" and set(
                roles.last_evidence_tool_calls
            ) == set(bundle.insight.evidence_event_ids) and len(roles.invocations) == 2
            shadow_ready = (
                roles.last_shadow_assessment is not None
                and roles.last_shadow_assessment.publishable is False
                and roles.last_authored_candidate is not None
            )
            if not valid or not shadow_ready:
                print("FAIL: required role execution or shadow candidate not confirmed")
                return 1
            print("PASS: evidence tool, both specialist roles and verifier completed")
            if roles.last_grounding_result is not None and not roles.last_grounding_result.eligible:
                print("NOTE: model-authored prose outside bounded grammar; not eligible for publication")
            if any(inv.input_tokens is None or inv.output_tokens is None
                   for inv in roles.invocations):
                print("NOTE: SDK usage unavailable; null is NOT zero billed tokens")
            return 0
        except Exception as exc:  # noqa: BLE001 - sanitize arbitrary provider/SDK failures
            # Do not print exception messages: authentication/HTTP exceptions may contain secrets.
            report = sanitized_failure(exc)
            # The recorded evidence IDs are trusted synthetic fixture IDs,
            # never raw tool arguments or model-generated response text.
            report["model_initiated_evidence_tool_calls"] = list(
                roles.last_evidence_tool_calls
            )
            report["expected_evidence_event_ids"] = list(
                bundle.insight.evidence_event_ids
            )
            report["last_attempted_role"] = roles.last_attempted_role
            report["attempted_role_count"] = sum(roles._attempts.values())
            report["completed_roles"] = [item.role for item in roles.invocations]
            print("FAIL: " + json.dumps(report, sort_keys=True))
            return 1
    
    finally:
        await project_client.close()
        await credential.close()

def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
