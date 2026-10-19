"""The isolated Foundry smoke command must be offline by default."""
import asyncio

import pytest

from pitchvolt import foundry_smoke


def test_smoke_dry_run_requires_no_sdk_or_endpoint(capsys) -> None:
    assert asyncio.run(foundry_smoke.run([])) == 0
    output = capsys.readouterr().out
    assert '"mode": "DRY_RUN"' in output
    assert '"http_max_retries": 0' in output
    assert "No Azure credentials loaded" in output
    assert "\"analyst_max_output_tokens\": 6144" in output


def test_smoke_requires_explicit_two_part_live_opt_in() -> None:
    with pytest.raises(SystemExit, match="acknowledge-billable-inference"):
        asyncio.run(foundry_smoke.run(["--execute"]))


def test_smoke_uses_single_real_synthetic_bundle() -> None:
    bundle = foundry_smoke.fixture()
    assert bundle.events
    assert tuple(event.event_id for event in bundle.events) == (
        bundle.insight.evidence_event_ids
    )


def test_live_smoke_explicitly_uses_azure_cli_credential_source() -> None:
    from pathlib import Path

    adapter = Path(foundry_smoke.__file__).with_name("foundry_adapter.py").read_text()
    smoke = Path(foundry_smoke.__file__).read_text()
    assert "credential: object | None = None" in adapter
    assert "credential = AzureCliCredential()" in smoke
    assert "from azure.identity.aio import AzureCliCredential" in smoke
    assert "from azure.ai.projects.aio import AIProjectClient" in smoke
    assert 'kwargs["max_retries"] = SMOKE_SETTINGS.http_max_retries' in smoke
    assert "project_client=project_client" in smoke
    assert "await project_client.close()" in smoke
    assert "await credential.close()" in smoke
    assert "DefaultAzureCredential()" not in smoke


def test_error_metadata_allowlist_never_exposes_exception_body() -> None:
    secret = "private-sample-token"
    underlying = RuntimeError(secret)
    underlying.status_code = 429
    underlying.code = "rate_limit_exceeded"
    try:
        raise ValueError("Authorization: " + secret) from underlying
    except ValueError as exc:
        report = foundry_smoke.sanitized_failure(exc)
    assert report["http_status"] == 429
    assert report["safe_error_code"] == "rate_limit_exceeded"
    assert secret not in str(report)


def test_unrecognized_provider_error_code_suppressed() -> None:
    exc = RuntimeError("sensitive request payload")
    exc.code = "user-supplied-sensitive-id"
    report = foundry_smoke.sanitized_failure(exc)
    assert report["safe_error_code"] is None
    assert "sensitive" not in str(report)


def test_smoke_token_budget_is_isolated_from_production_defaults() -> None:
    from pitchvolt.foundry_config import SMOKE_SETTINGS, FoundryConfig, RoleSettings

    assert SMOKE_SETTINGS.analyst_output_tokens == 6144
    assert SMOKE_SETTINGS.storyteller_output_tokens == 1024
    assert SMOKE_SETTINGS.timeout_seconds_per_role == 30.0
    assert SMOKE_SETTINGS.analyst_deployment == "matchpulse-gpt5-mini"
    assert SMOKE_SETTINGS.storyteller_deployment == "matchpulse-gpt4o"
    assert SMOKE_SETTINGS.http_max_retries == 0
    assert RoleSettings().max_output_tokens == 256
    assert FoundryConfig(
        project_endpoint="https://example.services.ai.azure.com/api/projects/sample",
        model_deployment="example",
    ).settings_for("analyst").max_output_tokens == 256


def test_validation_diagnostics_strips_secret_values_and_messages() -> None:
    from pydantic import BaseModel, ValidationError

    class TestSchema(BaseModel):
        number: int

    secret = "sensitive-provider-payload"
    with pytest.raises(ValidationError) as caught:
        TestSchema.model_validate({"number": secret})
    report = foundry_smoke.sanitized_failure(caught.value)
    assert report["validation_diagnostics"] == [
        {"type": "int_parsing", "location_depth": 1}
    ]
    assert secret not in str(report)
    assert "number" not in str(report)


def test_wrapped_pydantic_error_exposes_only_safe_category() -> None:
    from pydantic import BaseModel, ValidationError

    class TestSchema(BaseModel):
        count: int

    with pytest.raises(ValidationError) as caught:
        TestSchema.model_validate({"count": "secret"})
    try:
        raise RuntimeError("raw provider response secret") from caught.value
    except RuntimeError as exc:
        report = foundry_smoke.sanitized_failure(exc)
    assert report["exception_type"] == "RuntimeError"
    assert report["cause_type"] == "ValidationError"
    assert report["validation_diagnostics"][0]["type"] == "int_parsing"
    assert "secret" not in str(report)



def test_live_flag_rejects_documentation_endpoint_before_creating_credentials(capsys) -> None:
    endpoint = "https://YOUR-ACCOUNT.services.ai.azure.com/api/projects/YOUR-PROJECT"
    result = asyncio.run(foundry_smoke.run([
        "--execute", "--acknowledge-billable-inference", "--project-endpoint", endpoint,
    ]))
    output = capsys.readouterr().out
    assert result == 2
    assert "BLOCKED" in output
    assert "AUTH:" not in output
    assert endpoint not in output


def test_shadow_assertion_summary_never_prints_model_prose() -> None:
    from pitchvolt.assertion_audit import AssertionAudit, AssertionFinding, AssertionStatus

    secret = "PRIVATE_MODEL_GENERATED_TEXT"
    audit = AssertionAudit(findings=(AssertionFinding(
        excerpt=secret, status=AssertionStatus.UNVERIFIABLE, basis=secret,
    ),), complete_coverage=False)
    report = foundry_smoke.safe_assertion_audit(audit)
    assert report == {
        "finding_count": 1,
        "finding_statuses": ["unverifiable"],
        "complete_coverage": False,
        "publishable": False,
    }
    assert secret not in str(report)


def test_machine_report_writes_only_bounded_metadata(tmp_path) -> None:
    import json

    dest = tmp_path / "merge-smoke.json"
    report = {"smoke_status": "PASS", "source": "controlled",
              "token_usage_status": "unavailable_or_partial"}
    foundry_smoke.write_machine_report(str(dest), report)
    assert json.loads(dest.read_text()) == report
    assert dest.stat().st_mode & 0o777 == 0o600


def test_ci_report_refuses_unverified_model_prose_even_offline(tmp_path) -> None:
    with pytest.raises(SystemExit, match="Cannot export model-authored prose"):
        asyncio.run(foundry_smoke.run([
            "--report-file", str(tmp_path / "report.json"), "--show-unverified-prose",
        ]))
    assert not (tmp_path / "report.json").exists()
