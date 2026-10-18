"""Offline evaluator provides explicit baselines without any model calls."""
import json

import pytest

from pitchvolt.narrative_eval import EvaluationCase, benchmark_cases, evaluate, main
from pitchvolt.shadow_validation import ShadowStatus


def test_benchmark_classifies_synthetic_negatives_and_never_publishes() -> None:
    report = evaluate(benchmark_cases())
    assert report["total"] == 4
    assert report["invalid_claims"] == 2
    assert report["unverified_prose"] == 2
    assert report["publishable"] == 0
    assert report["semantic_verification"] == "not_implemented"
    assert all(row["publishable"] is False for row in report["results"])


def test_benchmark_output_is_reproducible_and_serializable(capsys) -> None:
    main()
    first = capsys.readouterr().out
    main()
    assert capsys.readouterr().out == first
    assert json.loads(first)["total"] == 4


def test_evaluator_rejects_incorrect_expected_verdict() -> None:
    original = benchmark_cases()[0]
    invalid = EvaluationCase(
        "mislabelled", original.candidate, original.evidence, ShadowStatus.INVALID_CLAIMS
    )
    with pytest.raises(ValueError, match="Unexpected shadow outcome"):
        evaluate((invalid,))


def test_evaluator_rejects_empty_or_duplicate_cases() -> None:
    with pytest.raises(ValueError, match="uniquely named"):
        evaluate(())
    original = benchmark_cases()[0]
    with pytest.raises(ValueError, match="uniquely named"):
        evaluate((original, original))
