"""The isolated Foundry smoke command must be offline by default."""
import asyncio

import pytest

from matchpulse import foundry_smoke


def test_smoke_dry_run_requires_no_sdk_or_endpoint(capsys) -> None:
    assert asyncio.run(foundry_smoke.run([])) == 0
    output = capsys.readouterr().out
    assert '"mode": "DRY_RUN"' in output
    assert '"http_max_retries": 2' in output
    assert "No Azure credentials loaded" in output
    assert "\"analyst_max_output_tokens\": 4096" in output


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
    assert 'kwargs["max_retries"] = SMOKE_HTTP_MAX_RETRIES' in smoke
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
    from matchpulse.foundry_config import FoundryConfig, RoleSettings

    assert foundry_smoke.SMOKE_ANALYST_OUTPUT_TOKENS == 4096
    assert foundry_smoke.SMOKE_HTTP_MAX_RETRIES == 2
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
