"""Streaming, deterministic tactical insight detection.

One stateful processor is the single source of truth for accepted events and insights.
No inference service, provider schema, or UI is imported here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from matchpulse.events import EventType, MatchEvent, MatchMetadata, Outcome


class InsightKind(StrEnum):
    HIGH_PRESS = "high_press"
    COUNTERATTACK = "counterattack"
    SUSTAINED_POSSESSION = "sustained_possession"


@dataclass(frozen=True)
class TacticalInsight:
    insight_id: str
    kind: InsightKind
    match_id: str
    team_id: str
    period: int
    clock_ms: int
    evidence_event_ids: tuple[str, ...]
    metrics: dict[str, int | float]


@dataclass
class MatchProcessor:
    match: MatchMetadata
    events: list[MatchEvent] = field(default_factory=list)
    insights: list[TacticalInsight] = field(default_factory=list)
    possession_team: str | None = None

    def ingest(self, event: MatchEvent) -> list[TacticalInsight]:
        """Reject invalid event streams before mutating state; emit only new insights."""
        expected = len(self.events) + 1
        if event.match_id != self.match.match_id or event.sequence != expected:
            raise ValueError("Invalid match or event sequence")
        if self.events and (event.period, event.clock_ms) < (
            self.events[-1].period, self.events[-1].clock_ms
        ):
            raise ValueError("Event clock moved backward")
        teams = {self.match.home_team_id, self.match.away_team_id}
        if event.team_id not in teams or event.possession_team_id not in teams:
            raise ValueError("Unknown team")
        if any(previous.event_id == event.event_id for previous in self.events):
            raise ValueError("Duplicate event ID")
        if event.event_type == EventType.TURNOVER and event.team_id != event.possession_team_id:
            raise ValueError("A turnover must award possession to the recovering team")
        if (
            self.possession_team is not None
            and event.possession_team_id != self.possession_team
            and event.event_type != EventType.TURNOVER
        ):
            raise ValueError("Possession change must use an explicit turnover event")
        self.events.append(event)
        self.possession_team = event.possession_team_id
        found = self._detect()
        self.insights.extend(found)
        return found

    def _detect(self) -> list[TacticalInsight]:
        current = self.events[-1]
        if current.event_type not in (EventType.SHOT, EventType.GOAL):
            return []
        window = self.events[max(0, len(self.events) - 8) :]
        if any(event.period != current.period for event in window):
            return []
        if current.clock_ms - window[0].clock_ms > 45_000:
            return []
        kinds = [event.event_type for event in window]
        # A sustained phase is separately evidenced by uninterrupted possession,
        # sufficient passing and a final attempt. The same source window is used
        # by streaming, snapshots and the narrative evidence service.
        if (
            EventType.TURNOVER not in kinds
            and all(e.possession_team_id == current.team_id for e in window)
            and sum(k == EventType.PASS for k in kinds) >= 4
            and len(window) >= 6
        ):
            return [TacticalInsight(
                insight_id=f"{current.event_id}:{InsightKind.SUSTAINED_POSSESSION.value}",
                kind=InsightKind.SUSTAINED_POSSESSION,
                match_id=current.match_id,
                team_id=current.team_id,
                period=current.period,
                clock_ms=current.clock_ms,
                evidence_event_ids=tuple(e.event_id for e in window),
                metrics={
                    "sequence_duration_ms": current.clock_ms - window[0].clock_ms,
                    "passes": sum(k == EventType.PASS for k in kinds),
                },
            )]
        try:
            turnover_idx = max(i for i, kind in enumerate(kinds) if kind == EventType.TURNOVER)
        except ValueError:
            return []
        turnover = window[turnover_idx]
        if turnover.team_id != current.team_id:
            return []
        attack = window[turnover_idx:]
        if any(e.possession_team_id != current.team_id for e in attack):
            return []
        if len(attack) < 3:
            return []
        preceding = window[:turnover_idx]
        pressured = any(
            e.event_type == EventType.PRESSURE and e.team_id == current.team_id
            for e in preceding
        ) and any(
            e.event_type == EventType.PASS and e.outcome == Outcome.FAILURE
            and e.team_id != current.team_id and e.evidence.get("under_pressure") is True
            for e in preceding
        )
        kind = InsightKind.HIGH_PRESS if pressured else InsightKind.COUNTERATTACK
        evidence = tuple(e.event_id for e in window if e in (preceding + attack))
        return [
            TacticalInsight(
                insight_id=f"{current.event_id}:{kind.value}",
                kind=kind,
                match_id=current.match_id,
                team_id=current.team_id,
                period=current.period,
                clock_ms=current.clock_ms,
                evidence_event_ids=evidence,
                metrics={
                    "transition_duration_ms": current.clock_ms - turnover.clock_ms,
                    "attacking_actions": len(attack),
                },
            )
        ]


def analyze_stream(match: MatchMetadata, events: list[MatchEvent]) -> list[TacticalInsight]:
    """Batch and streaming use precisely the same detection rules (DRY)."""
    processor = MatchProcessor(match=match)
    for event in events:
        processor.ingest(event)
    return processor.insights
