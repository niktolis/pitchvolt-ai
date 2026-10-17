import { describe, expect, it } from "vitest";

import type { ReplayMessage } from "../api/types";
import {
  atOrBefore,
  clampCursor,
  isEvidenceVisible,
  latestAtCursor,
  matchBounds,
  visibleNarrativeIds,
} from "./replayClock";

const event = (id: number, clock: number): ReplayMessage =>
  ({
    id,
    kind: "match_event",
    match_id: "fictional-match",
    payload: { event_id: `event-${id}`, clock_ms: clock },
  }) as ReplayMessage;

const insight = (id: number, clock: number): ReplayMessage =>
  ({
    id,
    kind: "tactical_insight",
    match_id: "fictional-match",
    payload: { insight_id: `insight-${id}`, clock_ms: clock },
  }) as ReplayMessage;

describe("canonical replay cursor", () => {
  const timeline = [event(1, 1_000), event(2, 5_000), insight(3, 5_000), event(4, 8_000)];

  it("hides future actions, insights and their narratives when seeking backwards", () => {
    expect(latestAtCursor(timeline, 8_000).insight?.insight_id).toBe("insight-3");
    const back = latestAtCursor(timeline, 3_000);
    expect(back.visible.map((item) => item.id)).toEqual([1]);
    expect(back.event?.event_id).toBe("event-1");
    expect(back.insight).toBeNull();
    expect(visibleNarrativeIds(timeline, 3_000).size).toBe(0);
    expect(isEvidenceVisible(timeline, 3_000, "insight-3")).toBe(false);
    expect(isEvidenceVisible(timeline, 5_000, "insight-3")).toBe(true);
  });

  it("shows tied action and insight only at their exact publication time", () => {
    expect(atOrBefore(timeline, 4_999).map((item) => item.id)).toEqual([1]);
    expect(atOrBefore(timeline, 5_000).map((item) => item.id)).toEqual([1, 2, 3]);
    expect(visibleNarrativeIds(timeline, 5_000).has("insight-3")).toBe(true);
  });

  it("clamps rewind, fast-forward and empty playback bounds", () => {
    expect(matchBounds(timeline)).toEqual({ start: 1_000, end: 8_000 });
    expect(matchBounds([])).toEqual({ start: 0, end: 0 });
    expect(clampCursor(-2_000, 1_000, 8_000)).toBe(1_000);
    expect(clampCursor(10_000, 1_000, 8_000)).toBe(8_000);
    expect(() => clampCursor(Number.NaN, 1_000, 8_000)).toThrow();
  });
});
