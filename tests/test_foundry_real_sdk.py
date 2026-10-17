"""Installed-SDK smoke construction contract; no authentication or HTTP requests."""
from __future__ import annotations

import asyncio

from matchpulse.foundry_adapter import FoundryConfig, FoundryRoles
from matchpulse.foundry_smoke import create_smoke_project_client


def test_actual_foundry_sdk_uses_async_zero_retry_clients_for_both_roles() -> None:
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
