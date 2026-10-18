"""Zero-network preflight; SDK envelopes simulated without Azure calls."""
from __future__ import annotations

import asyncio
import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from pitchvolt import foundry_preflight
from pitchvolt.foundry_adapter import FoundryRoles, sanitized_response_metadata, usage_counts
from pitchvolt.foundry_config import SMOKE_SETTINGS, isolated_foundry_config
from pitchvolt.foundry_smoke import fixture
from pitchvolt.narrative import Audience, InMemoryEvidenceTool
from pitchvolt.workflow import Orchestrator


def test_preflight_is_offline_and_redacts_project_identity(monkeypatch, capsys):
    def version(name: str) -> str:
        assert name in foundry_preflight.REQUIRED_DISTRIBUTIONS
        return "test-installed"

    monkeypatch.setattr(foundry_preflight.metadata, "version", version)
    endpoint = "https://private-account.services.ai.azure.com/api/projects/private-project"
    assert foundry_preflight.main(["--project-endpoint", endpoint]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "READY_FOR_OPERATOR_APPROVAL"
    assert report["endpoint_is_valid_project_url"]
    assert report["cloud_requests_made"] == 0
    assert report["billable_inference_permitted"] is False
    assert report["http_max_retries"] == 0
    assert report["evidence_event_count"] == len(fixture().events)
    assert endpoint not in json.dumps(report)
    assert "private-account" not in json.dumps(report)


@pytest.mark.parametrize("endpoint", [
    "", "https://example.services.ai.azure.com",
    "https://example.services.ai.azure.com/api/projects",
    "https://example.services.ai.azure.com/openai/v1/",
    "https://example.services.ai.azure.com/api/projects/p?key=secret",
    "https://user:secret@example.services.ai.azure.com/api/projects/p",
])
def test_preflight_blocks_invalid_or_missing_endpoint(monkeypatch, endpoint):
    monkeypatch.setattr(foundry_preflight.metadata, "version", lambda name: "installed")
    result = foundry_preflight.evaluate(endpoint)
    assert result["status"] == "BLOCKED"
    assert not result["endpoint_is_valid_project_url"]
    assert endpoint not in json.dumps(result) if endpoint else True


def test_preflight_missing_optional_sdk_fails_closed(monkeypatch):
    def missing(name: str) -> str:
        raise foundry_preflight.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(foundry_preflight.metadata, "version", missing)
    report = foundry_preflight.evaluate(
        "https://example.services.ai.azure.com/api/projects/p"
    )
    assert report["status"] == "BLOCKED"
    assert set(report["dependencies"]) == set(foundry_preflight.REQUIRED_DISTRIBUTIONS)
    assert all(v is None for v in report["dependencies"].values())


def test_usage_aggregation_never_understates_multi_message_rounds():
    msg = lambda a, b: SimpleNamespace(usage={"input_tokens": a, "output_tokens": b})
    messages = [msg(10, 5), msg(30, 7)]
    assert usage_counts(SimpleNamespace(messages=messages)) == (40, 12)
    assert usage_counts(SimpleNamespace(
        messages=messages, usage={"input_tokens": 100, "output_tokens": 30}
    )) == (100, 30)
    assert usage_counts(SimpleNamespace(messages=[msg(10, 5), SimpleNamespace()])) == (
        None, None
    )
    assert usage_counts(SimpleNamespace(messages=[msg(10, 5), SimpleNamespace(
        usage={"input_tokens": 2}
    )])) == (None, None)
    assert usage_counts(SimpleNamespace(
        raw_response=SimpleNamespace(usage={"prompt_tokens": 40, "completion_tokens": 12}),
        messages=messages,
    )) == (40, 12)
    assert usage_counts(SimpleNamespace(
        usage={"input_tokens": True, "output_tokens": -1},
        messages=[SimpleNamespace(content="private")],
    )) == (None, None)
    assert "private" not in str(sanitized_response_metadata(
        SimpleNamespace(messages=[SimpleNamespace(content="private")])
    ))


@pytest.mark.parametrize("composition", ["complete", "partial", "missing_tool", "timeout"])
def test_full_two_agent_sdk_contract_offline(monkeypatch, composition):
    """Exercise actual provider/orchestrator with fake Agent SDK over six events.

    These calls are in-memory Python functions, not real Azure model inference.
    A malformed Storyteller composition MUST fall back and cannot publish.
    """
    bundle = fixture()
    inspected: list[str] = []
    calls: list[str] = []

    class FakeAgent:
        def __init__(self, **kwargs):
            self.name = kwargs["name"]

        async def run(self, prompt, *, options, tools=None):
            calls.append(self.name)
            assert options["response_format"].__name__ in {
                "AnalystPlan", "StorytellerSelection"
            }
            if self.name == "PitchVoltAnalyst":
                assert tools and len(tools) == 1
                ids = bundle.insight.evidence_event_ids
                for event_id in ids[:1] if composition == "missing_tool" else ids:
                    data = json.loads(tools[0](event_id))
                    assert data["event_id"] == event_id
                    inspected.append(event_id)
                if composition == "timeout":
                    raise TimeoutError("fake offline provider timeout")
                return SimpleNamespace(
                    value={
                        "insight_id": bundle.insight.insight_id,
                        "angle": "tactical",
                        "evidence_event_ids": list(ids),
                    },
                    usage={"input_tokens": 100, "output_tokens": 200},
                )
            return SimpleNamespace(
                value={
                    "insight_id": bundle.insight.insight_id,
                    "audience": "analyst",
                    "angle": "tactical",
                    "style": "technical",
                    "fact_order": (
                        ["team", "tactic", "transition", "actions"]
                        if composition == "complete" else ["transition", "actions"]
                    ),
                    "authored_headline": "Unsupported synthetic three-goal claim",
                    "authored_text": "The match ended 5-0, a claim not in evidence.",
                },
                usage={"input_tokens": 50, "output_tokens": 25},
            )

    class FakeClient:
        def __init__(self, **kwargs):
            self.model = kwargs["model"]

    framework = ModuleType("agent_framework")
    framework.Agent = FakeAgent
    foundry = ModuleType("agent_framework.foundry")
    foundry.FoundryChatClient = FakeClient
    azure = ModuleType("azure")
    identity = ModuleType("azure.identity")
    identity.DefaultAzureCredential = lambda: object()
    for name, module in (
        ("agent_framework", framework),
        ("agent_framework.foundry", foundry),
        ("azure", azure),
        ("azure.identity", identity),
    ):
        monkeypatch.setitem(sys.modules, name, module)

    config = isolated_foundry_config(
        "https://example.services.ai.azure.com/api/projects/offline",
        evidence_event_count=len(bundle.events),
        inference_approved=True,  # injected fake SDK only; no credentials/network
    )
    roles = FoundryRoles(config, credential=object())
    flow = Orchestrator(InMemoryEvidenceTool(lambda _: bundle), roles, roles)
    result = asyncio.run(flow.narrate(bundle.insight.insight_id, Audience.ANALYST))
    assert inspected == list(roles.last_evidence_tool_calls)
    assert all(event_id in bundle.insight.evidence_event_ids for event_id in inspected)
    assert result.narrative.evidence_event_ids == bundle.insight.evidence_event_ids
    assert "5-0" not in result.narrative.text
    assert "Unsupported synthetic" not in result.narrative.headline
    if composition == "complete":
        assert result.source == "controlled"
        assert [i.role for i in roles.invocations] == ["analyst", "storyteller"]
        assert [(i.input_tokens, i.output_tokens) for i in roles.invocations] == [
            (100, 200), (50, 25)
        ]
        assert roles.last_shadow_assessment is not None
        assert roles.last_shadow_assessment.publishable is False
        assert result.trace[-1].action == "publish"
        assert len(inspected) == len(bundle.insight.evidence_event_ids) == 6
    else:
        assert result.source == "fallback"
        assert result.trace[-1].action == "reject"
        assert result.rejection_reason
        if composition in ("partial", "missing_tool"):
            assert calls == ["PitchVoltAnalyst", "PitchVoltStoryteller"] if composition == "partial" else ["PitchVoltAnalyst"]
        else:
            assert calls == ["PitchVoltAnalyst"]
        if composition == "timeout":
            assert len(inspected) == 6
