"""Regression tests for merge-only inference and sanitized CI summaries."""
from pathlib import Path

from scripts.foundry_merge_summary import summary


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/foundry-merge-smoke.yml"


def test_foundry_workflow_invokes_only_after_merge_on_main() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request_target:" in workflow
    assert "types: [closed]" in workflow
    assert "branches: [main]" in workflow
    assert "github.event.pull_request.merged == true" in workflow
    assert "github.run_attempt == 1" in workflow
    assert "merge_commit_sha" in workflow
    assert "fetch-depth: 0" in workflow
    assert "git merge-base --is-ancestor" in workflow
    assert "id-token: write" in workflow
    assert "azure/login@v3" in workflow
    assert "--execute --acknowledge-billable-inference" in workflow
    assert "--report-file" in workflow
    assert "push:" not in workflow
    assert "workflow_dispatch:" not in workflow


def test_summary_excludes_model_generated_content_and_unknown_usage() -> None:
    secret = "MODEL_TEXT_DONT_RENDER"
    report = {
        "smoke_status": "PASS", "source": "controlled",
        "model_initiated_evidence_tool_calls": [f"e{i}" for i in range(6)],
        "expected_evidence_event_ids": [f"e{i}" for i in range(6)],
        "token_usage_status": "unavailable_or_partial",
        "invocations": [
            {"role": "analyst", "duration_ms": 14930.1,
             "input_tokens": None, "output_tokens": None},
            {"role": "storyteller", "duration_ms": 3840.6,
             "input_tokens": None, "output_tokens": None},
        ],
        "model_authored_shadow": {"text": secret},
        "rejection_reason": secret,
    }
    rendered = summary(report)
    assert "PASS" in rendered and "complete" in rendered
    assert "unavailable/partial (not zero billed)" in rendered
    assert "14930" in rendered
    assert secret not in rendered


def test_summary_missing_or_failure_report_is_not_success() -> None:
    assert "No machine report was produced" in summary(None)
    assert "| Result | FAIL |" in summary({"smoke_status": "FAIL"})
