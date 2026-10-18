"""GitHub merge-smoke summary from an explicitly sanitized JSON report.

Never render raw model output, provider exceptions, headers, prompts or tokens.
This tool does not initiate inference. It runs on both PASS and FAIL.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def summary(report: dict[str, object] | None) -> str:
    """Render a small allowlisted summary without trusting arbitrary model strings."""
    header = "## PitchVolt Foundry merge smoke\n\n"
    if report is None:
        return header + "**No machine report was produced.** Check authentication/preflight and job logs.\n"
    outcome = "PASS" if report.get("smoke_status") == "PASS" else "FAIL"
    source = "controlled" if report.get("source") == "controlled" else "fallback_or_unavailable"
    calls = report.get("model_initiated_evidence_tool_calls")
    expected = report.get("expected_evidence_event_ids")
    retrieved = (isinstance(calls, list) and isinstance(expected, list)
                 and len(calls) == len(expected) == 6 and len(set(calls)) == 6
                 and set(calls) == set(expected))
    rows = [
        ("Result", outcome),
        ("Verified publication", source),
        ("Six evidence tools", "complete" if retrieved else "incomplete/unknown"),
        ("SDK token usage", "complete" if report.get("token_usage_status") == "complete"
         else "unavailable/partial (not zero billed)"),
    ]
    output = header + "| Check | Result |\n|---|---|\n"
    output += "".join(f"| {name} | {value} |\n" for name, value in rows)
    invocations = report.get("invocations")
    if isinstance(invocations, list):
        output += "\n| Role | Duration (ms) | Input tokens | Output tokens |\n|---|---:|---:|---:|\n"
        for item in invocations[:2]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            if role not in ("analyst", "storyteller"):
                continue
            duration = item.get("duration_ms")
            ms = str(round(duration)) if isinstance(duration, (float, int)) else "unknown"
            def counter(key: str) -> str:
                value = item.get(key)
                return str(value) if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else "unknown"
            output += f"| {role} | {ms} | {counter('input_tokens')} | {counter('output_tokens')} |\n"
    output += "\nOriginal model-authored prose is shadow-only; this report never publishes it.\n"
    return output


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/foundry_merge_summary.py REPORT.json")
    path = Path(sys.argv[1])
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            report = None
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        report = None
    sys.stdout.write(summary(report))


if __name__ == "__main__":
    main()
