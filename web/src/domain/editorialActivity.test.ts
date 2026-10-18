import { describe, expect, it } from "vitest";
import type { MatchEvent, ReplayMessage } from "../api/types";
import { recentRecordedActions, recordedActionCopy } from "./editorialActivity";

const action = (
  id: number,
  at: number,
  eventType: MatchEvent["event_type"] = "pass",
  outcome: MatchEvent["outcome"] = "success",
): ReplayMessage =>
  ({
    id,
    match_id: "fictional-match",
    kind: "match_event",
    payload: {
      event_id: `event-${id}`,
      event_type: eventType,
      clock_ms: at,
      team_id: "harbor-fc",
      player_id: "harbor-6",
      outcome,
    },
  }) as ReplayMessage;

const insight = (id: number, at: number): ReplayMessage =>
  ({
    id,
    match_id: "fictional-match",
    kind: "tactical_insight",
    payload: { insight_id: `insight-${id}`, clock_ms: at },
  }) as ReplayMessage;

describe("recorded action editorial activity", () => {
  const timeline = [
    action(1, 1_000, "pressure", "neutral"),
    action(2, 2_000, "pass", "failure"),
    insight(3, 2_000),
    action(4, 3_000, "turnover", "success"),
    action(5, 6_000, "carry", "success"),
    insight(6, 6_000),
    action(7, 8_000, "shot", "failure"),
  ];

  it("shows verified actions before a tactical insight is published", () => {
    expect(recentRecordedActions(timeline, 1_000).map((m) => m.id)).toEqual([1]);
    expect(recentRecordedActions(timeline, 1_999).map((m) => m.id)).toEqual([1]);
    expect(recentRecordedActions(timeline, 3_000).map((m) => m.id)).toEqual([4, 2, 1]);
  });

  it("never leaks future actions, including across backward seeks", () => {
    expect(recentRecordedActions(timeline, 8_000).map((m) => m.id)).toEqual([7, 5, 4]);
    expect(recentRecordedActions(timeline, 2_000).map((m) => m.id)).toEqual([2, 1]);
    expect(recentRecordedActions(timeline, 0)).toEqual([]);
    expect(recentRecordedActions([], 8_000)).toEqual([]);
  });

  it("excludes all insights regardless of source timestamp or result", () => {
    expect(recentRecordedActions([insight(10, 1_000)], 5_000)).toEqual([]);
    expect(recentRecordedActions(timeline, 6_000).map((m) => m.id)).toEqual([5, 4, 2]);
    expect(recentRecordedActions(timeline, 6_000, 1).map((m) => m.id)).toEqual([5]);
    expect(recentRecordedActions(timeline, 6_000, 0)).toEqual([]);
    expect(recentRecordedActions(timeline, Number.NaN)).toEqual([]);
  });

  it("preserves source event order for tied clocks without inventing events", () => {
    expect(
      recentRecordedActions([action(8, 1_000), action(9, 1_000), insight(10, 1_000)], 1_000).map(
        (m) => m.payload.event_id,
      ),
    ).toEqual(["event-9", "event-8"]);
  });

  it("uses only exact source fields and does not infer event outcome", () => {
    expect(
      recordedActionCopy(action(1, 51_050, "pressure", "neutral").payload as MatchEvent),
    ).toEqual({
        heading: "Harbor FC · pressure",
        detail: "Recorded action",
        time: "0:51",
      });
    expect(
      recordedActionCopy(action(2, 3_600_000, "pass", "failure").payload as MatchEvent),
    ).toEqual({
        heading: "Harbor FC · pass",
        detail: "Recorded failure",
        time: "60:00",
      });
    expect(
      recordedActionCopy(action(3, 4_000_000, "goal", "success").payload as MatchEvent).detail,
    ).toBe("Recorded success");
  });
});
