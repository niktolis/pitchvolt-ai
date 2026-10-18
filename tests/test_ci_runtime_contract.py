"""Release workflow contract: immutable Node image, stable CI, no auto screenshots."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE_VERSION = (ROOT / ".node-version").read_text(encoding="utf-8").strip()
WORKFLOWS = (
    ".github/workflows/python-checks.yml",
    ".github/workflows/frontend-checks.yml",
    ".github/workflows/d2-architecture.yml",
    ".github/workflows/azure-container-apps-deploy.yml",
)


def test_node_toolchain_version_is_consistent() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", NODE_VERSION)
    package = json.loads((ROOT / "web/package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "web/package-lock.json").read_text(encoding="utf-8"))
    expected_engine = f">={NODE_VERSION} <{int(NODE_VERSION.split('.')[0]) + 1}"
    assert package["engines"]["node"] == expected_engine
    assert lock["packages"][""]["engines"]["node"] == expected_engine
    dockerfile = (ROOT / "docker/backend.Dockerfile").read_text(encoding="utf-8")
    assert re.search(
        rf"^ARG NODE_IMAGE=node:{re.escape(NODE_VERSION)}-bookworm-slim"
        r"@sha256:[0-9a-f]{64}$",
        dockerfile,
        re.MULTILINE,
    )
    for path in ("frontend-checks.yml", "azure-container-apps-deploy.yml"):
        workflow = (ROOT / ".github/workflows" / path).read_text(encoding="utf-8")
        assert "node-version-file: .node-version" in workflow
        assert "node-version: '24." not in workflow


def test_actions_are_modern_and_runner_is_deterministic() -> None:
    for path in WORKFLOWS:
        workflow = (ROOT / path).read_text(encoding="utf-8")
        assert "runs-on: ubuntu-latest" not in workflow
        assert "runs-on: ubuntu-24.04" in workflow
        assert "actions/checkout@v7" in workflow
        assert "actions/checkout@v4" not in workflow
        assert "actions/setup-python@v5" not in workflow
        assert "actions/setup-node@v4" not in workflow
        assert "astral-sh/setup-uv@v6" not in workflow
    deployment = (ROOT / ".github/workflows/azure-container-apps-deploy.yml").read_text(
        encoding="utf-8"
    )
    assert "azure/login@v3" in deployment
    assert "docker/setup-buildx-action@v4" in deployment


def test_deployment_is_nonvisual_and_retains_release_health_gates() -> None:
    deployment = (ROOT / ".github/workflows/azure-container-apps-deploy.yml").read_text(
        encoding="utf-8"
    )
    assert "visual-evidence:" not in deployment
    assert "capture-live-visual.py" not in deployment
    assert "playwright" not in deployment
    assert "actions/upload-artifact" not in deployment
    assert 'az containerapp update --resource-group "$AZURE_RG" --name "$AZURE_APP"' in deployment
    assert "Wait for exact release on public domain" in deployment
    assert "Verify deployed health endpoint" in deployment
    assert "PITCHVOLT_NARRATIVE_PROVIDER: local" in deployment
