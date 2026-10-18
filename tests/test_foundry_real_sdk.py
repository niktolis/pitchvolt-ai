"""Installed-SDK smoke construction contract; no authentication or HTTP requests."""
from __future__ import annotations

import asyncio

import pytest

from pitchvolt.foundry_adapter import FoundryConfig, FoundryRoles
from pitchvolt.foundry_smoke import create_smoke_project_client


def test_actual_foundry_sdk_uses_async_bounded_retry_clients_for_both_roles() -> None:
    pytest.importorskip("azure.identity.aio")
    from azure.identity.aio import AzureCliCredential
    from openai import AsyncOpenAI

    async def exercise() -> None:
        endpoint = "https://example.services.ai.azure.com/api/projects/offline"
        credential = AzureCliCredential()
        project_client = create_smoke_project_client(endpoint, credential)
        try:
            roles = FoundryRoles(
                FoundryConfig(
                    project_endpoint=endpoint,
                    model_deployment="offline-analyst",
                    storyteller_model_deployment="offline-storyteller",
                    inference_explicitly_approved=True,
                ),
                credential=credential,
                project_client=project_client,
            )
            for role, expected_model in (
                ("analyst", "offline-analyst"),
                ("storyteller", "offline-storyteller"),
            ):
                agent = roles._agents[role]
                client = agent.client.client
                assert isinstance(client, AsyncOpenAI)
                assert client.max_retries == 0
                assert client.base_url.host == "example.services.ai.azure.com"
                assert "/api/projects/offline/openai/v1" in str(client.base_url)
                assert roles._config.role_deployments[role] == expected_model
        finally:
            await project_client.close()
            await credential.close()

    asyncio.run(exercise())


def test_real_installed_sdk_offline_preflight_has_no_model_access() -> None:
    # The shared minimal CI job intentionally excludes the optional SDK.
    # The later installed-SDK validation step executes this test for real.
    pytest.importorskip("azure.identity.aio")
    from pitchvolt.foundry_preflight import evaluate

    report = evaluate("https://offline-fixture.services.ai.azure.com/api/projects/contract-check")
    assert report["status"] == "READY_FOR_OPERATOR_APPROVAL"
    assert report["cloud_requests_made"] == 0
    assert not report["billable_inference_permitted"]
    assert report["http_max_retries"] == 0
    assert report["endpoint_value_redacted"]
