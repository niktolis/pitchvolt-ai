"""Reproducible, cost-free shadow benchmark for proposed narrative claims.

This measures structured factual grounding only. It cannot evaluate prose semantics
and never authorizes AI text publication.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass

from matchpulse.intelligence import analyze_stream
from matchpulse.narrative import (
    Audience,
    Claim,
    ClaimKind,
    EvidenceBundle,
    NarrativeCandidate,
)
from matchpulse.scenarios import scenario
from matchpulse.shadow_validation import ShadowStatus, assess_candidate


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    candidate: NarrativeCandidate
    evidence: EvidenceBundle
    expected: ShadowStatus


def benchmark_cases() -> tuple[EvaluationCase, ...]:
    """Original fictional evidence, with one positive manifest and three attacks."""
    match, events = scenario("high_press")
    insight = analyze_stream(match, events)[0]
    index = {event.event_id: event for event in events}
    bundle = EvidenceBundle(
        insight, tuple(index[event_id] for event_id in insight.evidence_event_ids)
    )
    base = NarrativeCandidate(
        insight_id=insight.insight_id,
        audience=Audience.ANALYST,
        headline="Pressing transition",
        text="The team capitalized on a turnover.",
        evidence_event_ids=insight.evidence_event_ids,
        claims=(
            Claim(kind=ClaimKind.INSIGHT_KIND, key="kind", value=insight.kind.value),
            Claim(
                kind=ClaimKind.METRIC,
                key="attacking_actions",
                value=insight.metrics["attacking_actions"],
            ),
        ),
    )
    return (
        EvaluationCase("valid_manifest", base, bundle, ShadowStatus.UNVERIFIED_PROSE),
        EvaluationCase(
            "unsupported_metric",
            base.model_copy(update={
                "claims": (Claim(kind=ClaimKind.METRIC, key="attacking_actions", value=999),)
            }),
            bundle,
            ShadowStatus.INVALID_CLAIMS,
        ),
        EvaluationCase(
            "foreign_evidence",
            base.model_copy(update={"evidence_event_ids": ("fictional-invalid-id",)}),
            bundle,
            ShadowStatus.INVALID_CLAIMS,
        ),
        EvaluationCase(
            "plausible_manifest_false_prose",
            base.model_copy(update={
                "text": "Three goals were scored and possession was 90 percent."
            }),
            bundle,
            ShadowStatus.UNVERIFIED_PROSE,
        ),
    )


def evaluate(cases: tuple[EvaluationCase, ...]) -> dict[str, object]:
    """Fail closed if a fixture's expected classification regresses."""
    if not cases or len({case.name for case in cases}) != len(cases):
        raise ValueError("Benchmark requires nonempty, uniquely named cases")
    results: list[dict[str, str | bool]] = []
    for case in cases:
        result = assess_candidate(case.candidate, case.evidence)
        if result.publishable or result.status != case.expected:
            raise ValueError(f"Unexpected shadow outcome: {case.name}")
        results.append({
            "case": case.name,
            "status": result.status.value,
            "publishable": result.publishable,
        })
    counts = Counter(item["status"] for item in results)
    return {
        "total": len(results),
        "invalid_claims": counts[ShadowStatus.INVALID_CLAIMS.value],
        "unverified_prose": counts[ShadowStatus.UNVERIFIED_PROSE.value],
        "publishable": 0,
        "results": results,
        "semantic_verification": "not_implemented",
    }


def main() -> None:
    print(json.dumps(evaluate(benchmark_cases()), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
