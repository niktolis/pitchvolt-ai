"""StatsBomb-shaped *original synthetic* adapter and detector invariants.

These examples do not contain downloaded Open Data matches or records.
"""
from copy import deepcopy

import pytest
from pydantic import ValidationError

from matchpulse.events import EventType, Outcome, Point, Provenance
from matchpulse.intelligence import InsightKind, analyze_stream
from matchpulse.providers.statsbomb import (
    StatsBombSyntheticSource,
    point_to_statsbomb,
    statsbomb_to_point,
    synthetic_to_statsbomb,
)
from matchpulse.scenarios import scenario


def _fixture(name: str = "high_press"):
    match, native = scenario(name)
    raw = synthetic_to_statsbomb(match, native)
    provenance = Provenance(
        generator="test-statsbomb-shaped",
        generator_version="1",
        seed=42,
        scenario=name,
    )
    return match, native, raw, provenance


@pytest.mark.parametrize(
    ("xy", "expected"),
    [
        ([0.0, 0.0], Point(x=0, y=0)),
        ([120.0, 80.0], Point(x=105, y=68)),
        ([60.0, 40.0], Point(x=52.5, y=34)),
        ([80.0, 40.0], Point(x=70, y=34)),
    ],
)
def test_pitch_coordinates_use_physical_metres(xy, expected) -> None:
    assert statsbomb_to_point(xy) == expected
    assert point_to_statsbomb(expected) == xy


@pytest.mark.parametrize("xy", [
    [-0.1, 10], [120.001, 0], [0, 80.1], [float("nan"), 1],
    [float("inf"), 5], [True, 0], [1],
])
def test_malformed_statsbomb_coordinates_rejected(xy) -> None:
    with pytest.raises(ValueError):
        statsbomb_to_point(xy)


def test_statsbomb_synthetic_json_shape_and_reproducibility() -> None:
    match, native, records, prov = _fixture()
    assert records == synthetic_to_statsbomb(match, native)
    assert [r["type"]["name"] for r in records] == [
        "Pressure", "Pass", "Ball Recovery", "Carry", "Pass", "Shot",
    ]
    assert records[0]["index"] == 1
    assert records[0]["period"] == 2
    assert records[0]["minute"] == 67
    assert records[1]["under_pressure"] is True
    assert records[1]["pass"]["outcome"]["name"] == "Incomplete"
    assert records[2]["possession_team"]["name"] == "harbor-fc"
    assert records[2]["possession"] == 2
    assert records[-1]["shot"]["outcome"]["name"] == "Saved"
    assert len(records[-1]["shot"]["end_location"]) == 2  # no fabricated height
    assert all("matchpulse" not in record for record in records)
    events = StatsBombSyntheticSource(match, records, prov).events()
    assert [e.event_type for e in events] == [e.event_type for e in native]
    assert events[1].outcome == Outcome.FAILURE
    assert events[1].evidence["under_pressure"] is True
    assert events[-1].evidence["on_target"] is True
    assert all(e.provenance.source == "synthetic" for e in events)
    assert len({e.event_id for e in events}) == len(events)


@pytest.mark.parametrize("name", ["high_press", "counterattack", "sustained_possession"])
def test_adapter_preserves_detector_decisions_and_metrics(name: str) -> None:
    match, native, records, prov = _fixture(name)
    canonical = StatsBombSyntheticSource(match, records, prov).events()
    observed = analyze_stream(match, canonical)
    expected = analyze_stream(match, native)
    assert [e.kind for e in observed] == [e.kind for e in expected]
    assert [e.metrics for e in observed] == [e.metrics for e in expected]
    assert [e.clock_ms for e in canonical] == [e.clock_ms for e in native]
    assert [e.possession_team_id for e in canonical] == [
        e.possession_team_id for e in native
    ]
    assert [e.sequence for e in canonical] == list(range(1, len(canonical) + 1))
    for insight in observed:
        assert set(insight.evidence_event_ids).issubset({e.event_id for e in canonical})


def test_statsbomb_scenario_uses_same_truth_and_existing_stream() -> None:
    match, events = scenario("statsbomb_high_press")
    native_match, native = scenario("high_press")
    assert match.match_id != native_match.match_id
    assert events == scenario("statsbomb_high_press")[1]
    assert all(e.provenance.generator == "matchpulse-statsbomb-shaped" for e in events)
    statsbomb = analyze_stream(match, events)
    reference = analyze_stream(native_match, native)
    assert [e.kind for e in statsbomb] == [InsightKind.HIGH_PRESS]
    assert [e.metrics for e in statsbomb] == [e.metrics for e in reference]


def test_unsupported_event_is_not_silently_dropped() -> None:
    match, _, records, prov = _fixture()
    bad = deepcopy(records)
    bad[0]["type"] = {"id": 5, "name": "Camera On"}
    with pytest.raises(ValueError, match="Unsupported StatsBomb event"):
        StatsBombSyntheticSource(match, bad, prov).events()


def test_mismatched_type_identifiers_rejected() -> None:
    match, _, records, prov = _fixture()
    bad = deepcopy(records)
    bad[0]["type"]["id"] = 100
    with pytest.raises(ValueError, match="ID/name mismatch"):
        StatsBombSyntheticSource(match, bad, prov).events()


def test_incomplete_record_rejected_instead_of_inventing_pass_endpoint() -> None:
    match, _, records, prov = _fixture()
    bad = deepcopy(records)
    del bad[1]["pass"]
    with pytest.raises(ValueError, match="Pass requires"):
        StatsBombSyntheticSource(match, bad, prov).events()


def test_recovery_failure_is_not_treated_as_a_turnover() -> None:
    match, _, records, prov = _fixture()
    bad = deepcopy(records)
    bad[2]["ball_recovery"] = {"recovery_failure": True}
    with pytest.raises(ValueError, match="Failed Ball Recovery"):
        StatsBombSyntheticSource(match, bad, prov).events()


def test_possession_change_without_explicit_recovery_is_rejected() -> None:
    match, _, records, prov = _fixture()
    bad = deepcopy(records)
    # A raw possession-team switch without an actual Ball Recovery must never
    # become a fictitious counterattack.
    bad[2]["type"] = {"id": 43, "name": "Carry"}
    bad[2]["carry"] = {"end_location": [80, 40]}
    with pytest.raises(ValueError, match="explicit turnover"):
        StatsBombSyntheticSource(match, bad, prov).events()


def test_same_team_new_possession_number_is_not_a_turnover() -> None:
    match, _, records, prov = _fixture("sustained_possession")
    bad = deepcopy(records)
    for rec in bad[2:]:
        rec["possession"] = 2
    events = StatsBombSyntheticSource(match, bad, prov).events()
    assert [e.event_type for e in events].count(EventType.TURNOVER) == 0
    assert analyze_stream(match, events) == []


def test_missing_player_and_invalid_order_rejected() -> None:
    match, _, records, prov = _fixture()
    bad = deepcopy(records)
    del bad[0]["player"]
    with pytest.raises(ValidationError):
        StatsBombSyntheticSource(match, bad, prov).events()
    bad = deepcopy(records)
    bad[1]["index"] = 99
    with pytest.raises(ValueError, match="contiguous"):
        StatsBombSyntheticSource(match, bad, prov).events()


def test_malformed_period_timestamp_rejected() -> None:
    match, _, records, prov = _fixture()
    bad = deepcopy(records)
    bad[1]["timestamp"] = "bad"
    with pytest.raises(ValueError, match="Invalid StatsBomb timestamp"):
        StatsBombSyntheticSource(match, bad, prov).events()


def test_goals_are_shots_with_goal_outcome_in_statsbomb() -> None:
    match, native, _, prov = _fixture("counterattack")
    goal = native[-1].model_copy(update={
        "event_type": EventType.GOAL,
        "outcome": Outcome.SUCCESS,
    })
    with_goal = native[:-1] + [goal]
    raw = synthetic_to_statsbomb(match, with_goal)
    assert raw[-1]["type"]["name"] == "Shot"
    assert raw[-1]["shot"]["outcome"]["name"] == "Goal"
    canonical = StatsBombSyntheticSource(match, raw, prov).events()
    assert canonical[-1].event_type == EventType.GOAL
    assert canonical[-1].outcome == Outcome.SUCCESS
    assert [i.kind for i in analyze_stream(match, canonical)] == [InsightKind.COUNTERATTACK]


def test_synthetic_source_requires_synthetic_provenance() -> None:
    with pytest.raises(ValidationError, match="synthetic"):
        Provenance(
            generator="import", generator_version="1", seed=1,
            scenario="real-match", source="statsbomb-open-data",
        )


def test_shot_and_pass_outcome_ids_cannot_contradict_names() -> None:
    match, _, records, prov = _fixture()
    wrong_pass = deepcopy(records)
    wrong_pass[1]["pass"]["outcome"]["id"] = 75  # Out, not Incomplete
    with pytest.raises(ValueError, match="pass outcome ID/name mismatch"):
        StatsBombSyntheticSource(match, wrong_pass, prov).events()

    wrong_shot = deepcopy(records)
    wrong_shot[-1]["shot"]["outcome"]["id"] = 97  # Goal, not Saved
    with pytest.raises(ValueError, match="shot outcome ID/name mismatch"):
        StatsBombSyntheticSource(match, wrong_shot, prov).events()


def test_recovery_must_increment_source_possession_counter() -> None:
    match, _, records, prov = _fixture()
    bad = deepcopy(records)
    bad[2]["possession"] = 1
    with pytest.raises(ValueError, match="new team and new possession ID"):
        StatsBombSyntheticSource(match, bad, prov).events()


def test_inconsistent_team_id_mapping_rejected() -> None:
    match, _, records, prov = _fixture()
    bad = deepcopy(records)
    bad[1]["team"]["id"] = 9999
    with pytest.raises(ValueError, match="reference ID/name"):
        StatsBombSyntheticSource(match, bad, prov).events()


def test_period_relative_timestamp_cannot_disagree_with_match_minute() -> None:
    match, _, records, prov = _fixture()
    bad = deepcopy(records)
    bad[1]["timestamp"] = "00:00:" + bad[1]["timestamp"].split(":")[-1]
    with pytest.raises(ValueError, match="timestamp disagrees"):
        StatsBombSyntheticSource(match, bad, prov).events()
