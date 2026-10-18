"""Prevent accidental regression to the superseded product identity."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = "match" + "pulse"
# Names of existing cloud resources, not a claim of the product's branding.
EXISTING_AZURE = (
    "rg-" + LEGACY + "-dev",
    LEGACY + "a433a4e04d",
    LEGACY + "-web",
    LEGACY + "-acr-pull",
    LEGACY + "-github-actions-deploy",
    LEGACY + "-ai-resource",
    LEGACY + "-ai",
)
TEXT_EXTENSIONS = frozenset({
    ".py", ".toml", ".lock", ".md", ".json", ".yml", ".yaml",
    ".d2", ".svg", ".sh", ".html", ".tsx", ".ts", ".css",
})
ROOT_FILES = {"README.md", "pyproject.toml", "uv.lock", "compose.yaml"}
TREE_ROOTS = ("src", "tests", "scripts", "web", "docs", ".github", ".devcontainer", "docker")
IGNORED_PARTS = {".venv", "node_modules", "__pycache__", "dist", "build", ".pytest_cache"}


def test_project_identity_is_consistent() -> None:
    assert (ROOT / "src/pitchvolt/api.py").is_file()
    assert not (ROOT / ("src/" + LEGACY)).exists()
    assert 'name = "pitchvolt-ai"' in (ROOT / "pyproject.toml").read_text()
    assert 'name = "pitchvolt-ai"' in (ROOT / "uv.lock").read_text()
    assert '"name": "pitchvolt-web"' in (ROOT / "web/package-lock.json").read_text()
    assert '"title": "PitchVolt AI"' in (ROOT / "web/openapi.json").read_text()
    assert "github.com/niktolis/pitchvolt-ai/" in (ROOT / "README.md").read_text()


def test_no_old_product_identity_except_existing_cloud_resource_names() -> None:
    files = [ROOT / name for name in ROOT_FILES]
    for folder in TREE_ROOTS:
        files.extend((ROOT / folder).rglob("*"))
    offenders = []
    for path in files:
        if (not path.is_file() or path.suffix not in TEXT_EXTENSIONS
                or any(piece in IGNORED_PARTS for piece in path.parts)):
            continue
        content = path.read_text(encoding="utf-8")
        for name in EXISTING_AZURE:
            content = content.replace(name, "")
        # Historical OIDC principal and source repository are necessary only
        # in the operator migration runbook, not in active product references.
        if path == ROOT / "docs/repository-rename.md":
            content = content.replace("niktolis/" + LEGACY + "-ai", "")
        # Existing Entra identity details are not to be renamed by this PR.
        occurrences = re.findall(re.escape(LEGACY), content, re.IGNORECASE)
        if occurrences:
            offenders.append(f"{path.relative_to(ROOT)}: {len(occurrences)} stale names")
    assert not offenders, "Old project branding remains: " + ", ".join(offenders)
