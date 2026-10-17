"""Offline provider wiring tests: fake SDK modules, zero Azure requests."""
from __future__ import annotations

import asyncio
import sys
from types import ModuleType, SimpleNamespace

import pytest

from matchpulse.foundry_adapter import FoundryConfig, FoundryRoles
from matchpulse.narrative import Audience
from matchpulse.workflow import AnalystPlan, StorytellerSelection


def test_foundry_sdk_constructor_and_structured_calls_without_network(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    class FakeCredential:
        def __init__(self) -> None:
            calls.append(("credential", None))

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            calls.append(("client", kwargs))

    class FakeAgent:
        def __init__(self, **kwargs: object) -> None:
            self.name = kwargs["name"]
            calls.append(("agent", self.name))

        async def run(self, prompt: str, *, options: dict[str, object]) -> object:
            calls.append(("run", (self.name, options, prompt)))
            if self.name == "MatchPulseAnalyst":
                assert options["tools"][0]("event-1")
                return SimpleNamespace(value={
                    "insight_id": "insight-1",
                    "angle": "tactical",
                    "evidence_event_ids": ["event-1"],
                })
            return SimpleNamespace(value={
                "insight_id": "insight-1",
                "audience": "analyst",
                "angle": "tactical",
                "style": "technical",
            })

    framework = ModuleType("agent_framework")
    framework.Agent = FakeAgent  # type: ignore[attr-defined]
    foundry = ModuleType("agent_framework.foundry")
    foundry.FoundryChatClient = FakeClient  # type: ignore[attr-defined]
    azure = ModuleType("azure")
    identity = ModuleType("azure.identity")
    identity.DefaultAzureCredential = FakeCredential  # type: ignore[attr-defined]
    azure.identity = identity  # type: ignore[attr-defined]
    framework.foundry = foundry  # type: ignore[attr-defined]
    for name, module in (
        ("agent_framework", framework),
        ("agent_framework.foundry", foundry),
        ("azure", azure),
        ("azure.identity", identity),
    ):
        monkeypatch.setitem(sys.modules, name, module)

    roles = FoundryRoles(FoundryConfig(
        project_endpoint="https://example.services.ai.azure.com/api/projects/sample",
        model_deployment="test-model",
        inference_explicitly_approved=True,
        max_output_tokens_per_role=192,
    ))
    assert [kind for kind, _ in calls] == ["credential", "client", "client", "agent", "agent"]
    client_kwargs = calls[1][1]
    assert isinstance(client_kwargs, dict)
    assert client_kwargs["model"] == "test-model"
    assert calls[2][1]["model"] == "test-model"

    async def exercise() -> None:
        # These are fake SDK calls, not Azure requests or deployed models.
        plan = await roles.analyze(SimpleNamespace(insight=SimpleNamespace(
            insight_id="insight-1",
            kind=SimpleNamespace(value="high_press"),
            evidence_event_ids=("event-1",),
            metrics={"attacking_actions": 3},
        ), events=(SimpleNamespace(event_id="event-1", model_dump_json=lambda: '{"event_id":"event-1"}'),)))
        assert isinstance(plan, AnalystPlan)
        assert plan.evidence_event_ids == ("event-1",)
        selection = await roles.select(plan, None, Audience.ANALYST)
        assert isinstance(selection, StorytellerSelection)
        assert selection.style == "technical"

    asyncio.run(exercise())
    run_calls = [item for kind, item in calls if kind == "run"]
    assert len(run_calls) == 2
    for _, options, _ in run_calls:
        assert options["max_output_tokens"] == 192
    assert roles.last_evidence_tool_calls == ("event-1",)
    assert run_calls[0][1]["response_format"] is AnalystPlan
    assert run_calls[1][1]["response_format"] is StorytellerSelection


def test_missing_sdk_fails_only_after_explicit_opt_in(monkeypatch) -> None:
    # Import blocker is scoped to the SDK entrypoint and never opens a network connection.
    import builtins

    original_import = builtins.__import__

    def blocked(name: str, *args: object, **kwargs: object) -> object:
        if name == "agent_framework":
            raise ImportError("SDK absent")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(RuntimeError, match="Install the reviewed"):
        FoundryRoles(FoundryConfig(
            "https://example.services.ai.azure.com/api/projects/sample",
            "not-deployed",
            inference_explicitly_approved=True,
        ))


def test_heterogeneous_clients_and_optional_editorial_are_isolated(monkeypatch) -> None:
    import sys
    from types import ModuleType

    created: list[tuple[str, object]] = []

    class Credential:
        pass

    class Client:
        def __init__(self, **kwargs: object) -> None:
            created.append(("client", kwargs))

    class Agent:
        def __init__(self, **kwargs: object) -> None:
            created.append(("agent", kwargs["name"]))

    framework = ModuleType("agent_framework")
    framework.Agent = Agent  # type: ignore[attr-defined]
    foundry = ModuleType("agent_framework.foundry")
    foundry.FoundryChatClient = Client  # type: ignore[attr-defined]
    azure = ModuleType("azure")
    identity = ModuleType("azure.identity")
    identity.DefaultAzureCredential = Credential  # type: ignore[attr-defined]
    for name, module in (
        ("agent_framework", framework),
        ("agent_framework.foundry", foundry),
        ("azure", azure),
        ("azure.identity", identity),
    ):
        monkeypatch.setitem(sys.modules, name, module)

    config = FoundryConfig(
        "https://example.services.ai.azure.com/api/projects/sample",
        "analyst-gpt5-mini",
        storyteller_model_deployment="storyteller-gpt4o-mini",
        editorial_model_deployment="editorial-test-only",
        inference_explicitly_approved=True,
    )
    roles = FoundryRoles(config)
    assert list(config.role_deployments) == ["analyst", "storyteller", "editorial"]
    clients = [value for kind, value in created if kind == "client"]
    assert [client["model"] for client in clients] == [
        "analyst-gpt5-mini", "storyteller-gpt4o-mini", "editorial-test-only",
    ]
    assert len({id(client["credential"]) for client in clients}) == 1
    assert [name for kind, name in created if kind == "agent"] == [
        "MatchPulseAnalyst", "MatchPulseStoryteller", "MatchPulseEditorial",
    ]
    assert roles._analyst is roles._agents["analyst"]
    assert roles._storyteller is roles._agents["storyteller"]
    assert config.max_inference_calls_per_narrative == 2
