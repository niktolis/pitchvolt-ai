"""Offline provider wiring tests: fake SDK modules, zero Azure requests."""
from __future__ import annotations

import asyncio
import sys
from types import ModuleType, SimpleNamespace

import pytest

from pitchvolt.foundry_adapter import FoundryConfig, FoundryRoles
from pitchvolt.narrative import Audience
from pitchvolt.workflow import AnalystPlan, StorytellerSelection


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

        async def run(self, prompt: str, *, options: dict[str, object], tools=None) -> object:
            calls.append(("run", (self.name, options, prompt)))
            assert "tools" not in options
            if self.name == "PitchVoltAnalyst":
                assert tools is not None and tools[0]("event-1")
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
        evidence = SimpleNamespace(insight=SimpleNamespace(
            insight_id="insight-1",
            kind=SimpleNamespace(value="high_press"),
            evidence_event_ids=("event-1",),
            team_id="harbor-fc",
            metrics={"attacking_actions": 3, "transition_duration_ms": 9000},
        ), events=(SimpleNamespace(event_id="event-1", model_dump_json=lambda: '{"event_id":"event-1"}'),))
        plan = await roles.analyze(evidence)
        assert isinstance(plan, AnalystPlan)
        assert plan.evidence_event_ids == ("event-1",)
        selection = await roles.select(plan, evidence, Audience.ANALYST)
        assert isinstance(selection, StorytellerSelection)
        assert selection.style == "technical"

    asyncio.run(exercise())
    run_calls = [item for kind, item in calls if kind == "run"]
    assert len(run_calls) == 2
    for _, options, _ in run_calls:
        assert options["max_tokens"] == 192
        assert "max_output_tokens" not in options
    assert roles.last_evidence_tool_calls == ("event-1",)
    assert [item.role for item in roles.invocations] == ["analyst", "storyteller"]
    assert all(item.duration_ms >= 0 for item in roles.invocations)
    assert all(item.input_tokens is None for item in roles.invocations)
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
        "PitchVoltAnalyst", "PitchVoltStoryteller", "PitchVoltEditorial",
    ]
    assert roles._analyst is roles._agents["analyst"]
    assert roles._storyteller is roles._agents["storyteller"]
    assert config.max_inference_calls_per_narrative == 2


def test_sanitized_response_metadata_excludes_payload() -> None:
    from pitchvolt.foundry_adapter import sanitized_response_metadata

    payload = "SECRET generated answer or bearer token"
    response = SimpleNamespace(
        value=None, finish_reason="length", status="incomplete",
        messages=[SimpleNamespace(role="assistant", content=payload)],
        usage=SimpleNamespace(input_tokens=200, output_tokens=256, total_tokens=456),
        raw_response=payload,
    )
    metadata = sanitized_response_metadata(response)
    assert metadata["structured_value_present"] is False
    assert metadata["finish_reason"] == "length"
    assert metadata["response_status"] == "incomplete"
    assert metadata["output_tokens"] == 256
    assert metadata["message_count"] == 1
    assert payload not in str(metadata)


def test_response_metadata_unknown_status_and_missing_usage() -> None:
    from pitchvolt.foundry_adapter import sanitized_response_metadata

    response = SimpleNamespace(
        value=None, status="PRIVATE_USER_TEXT", finish_reason="PRIVATE_USER_TEXT",
        usage=None,
    )
    metadata = sanitized_response_metadata(response)
    assert metadata["response_status"] is None
    assert metadata["finish_reason"] is None
    assert metadata["input_tokens"] is None
    assert metadata["message_count"] == 0


def test_injected_project_client_only_when_requested(monkeypatch) -> None:
    from types import ModuleType

    seen: list[dict[str, object]] = []

    class FakeAgent:
        def __init__(self, **kwargs: object) -> None:
            pass

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            seen.append(kwargs)

    framework = ModuleType("agent_framework")
    framework.Agent = FakeAgent  # type: ignore[attr-defined]
    foundry = ModuleType("agent_framework.foundry")
    foundry.FoundryChatClient = FakeClient  # type: ignore[attr-defined]
    azure = ModuleType("azure")
    identity = ModuleType("azure.identity")
    identity.DefaultAzureCredential = lambda: object()  # type: ignore[attr-defined]
    for name, module in (("agent_framework", framework),
                         ("agent_framework.foundry", foundry),
                         ("azure", azure), ("azure.identity", identity)):
        monkeypatch.setitem(sys.modules, name, module)
    config = FoundryConfig(
        project_endpoint="https://example.services.ai.azure.com/api/projects/sample",
        model_deployment="test-model", inference_explicitly_approved=True,
    )
    injected = object()
    FoundryRoles(config, credential=object(), project_client=injected)
    assert len(seen) == 2
    assert all(call["project_client"] is injected for call in seen)
    seen.clear()
    FoundryRoles(config, credential=object())
    assert len(seen) == 2
    assert all("project_client" not in call for call in seen)
