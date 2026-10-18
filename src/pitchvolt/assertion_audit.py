"""Conservative offline lexical assertion audit for shadow-only football prose.

This is NOT general semantic entailment. Unsupported material prose is reported
as unverifiable. No outcome of this audit grants publication permission.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from pitchvolt.narrative import EvidenceBundle, NarrativeCandidate


class AssertionStatus(StrEnum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNVERIFIABLE = "unverifiable"


@dataclass(frozen=True)
class AssertionFinding:
    excerpt: str
    status: AssertionStatus
    basis: str


@dataclass(frozen=True)
class AssertionAudit:
    findings: tuple[AssertionFinding, ...]
    complete_coverage: bool
    publishable: bool = False


# Precisely scoped observations; unknown football concepts are intentionally
# not treated as supported. Canonical numbers live exclusively in the bundle.
_ACTIONS = re.compile(r"\b(\d+)\s+attacking actions?\b", re.IGNORECASE)
_TRANSITION = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(?:-|\s)*seconds?\b", re.IGNORECASE
)
_SCORE = re.compile(r"\b\d+\s*[-–:]\s*\d+\b")
_RISKY = re.compile(
    r"\b(?:won|lost|victory|defeat|dominat\w*|superior|best|worst|"
    r"goalkeeper|striker|scored|scoreline|outplay\w*|guaranteed|"
    r"clearly|undoubtedly)\b",
    re.IGNORECASE,
)


def audit_assertions(candidate: NarrativeCandidate, bundle: EvidenceBundle) -> AssertionAudit:
    """Identify some claims and classify them against immutable metrics.

    Deliberately conservative: not a full assertion extractor, so an unrecognized
    passage cannot be declared complete. Headline and prose are both inspected.
    """
    text = candidate.headline + "\n" + candidate.text
    findings: list[AssertionFinding] = []
    spans: list[tuple[int, int]] = []
    for pattern, key, scale in (
        (_ACTIONS, "attacking_actions", 1),
        (_TRANSITION, "transition_duration_ms", 1000),
    ):
        expected = bundle.insight.metrics.get(key)
        for match in pattern.finditer(text):
            actual = float(match.group(1)) * scale
            status = (
                AssertionStatus.SUPPORTED
                if expected is not None and actual == expected
                else AssertionStatus.CONTRADICTED
            )
            findings.append(AssertionFinding(match.group(0), status, key))
            spans.append(match.span())
    for match in _SCORE.finditer(text):
        findings.append(AssertionFinding(match.group(0), AssertionStatus.UNVERIFIABLE, "scoreline not in evidence contract"))
        spans.append(match.span())
    for match in _RISKY.finditer(text):
        if any(start <= match.start() < end for start, end in spans):
            continue
        findings.append(AssertionFinding(match.group(0), AssertionStatus.UNVERIFIABLE, "unsupported football assertion"))
    # Unknown natural language may contain claims that lexical recognition misses.
    # Therefore coverage is always false in this initial, offline research phase.
    return AssertionAudit(tuple(findings), complete_coverage=False)
