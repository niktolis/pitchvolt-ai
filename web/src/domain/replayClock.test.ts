import { describe, expect, it } from "vitest";

import type { ReplayMessage } from "../api/types";
import {
  atOrBefore,
  clampCursor,
  isEvidenceVisible,
  latestAtCursor,
  matchBounds,
  narrativeStateKey,
  publishedNarrativeAtCursor,
  recentInsightsAtCursor,
  selectedAtCursor,
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

  it("uses only published insights and caps the broadcast feed", () => {
    const many = [
      insight(11, 1_000),
      insight(12, 2_000),
      event(13, 3_000),
      insight(14, 4_000),
      insight(15, 5_000),
      insight(16, 6_000),
    ];
    expect(recentInsightsAtCursor(many, 4_500).map((m) => m.id)).toEqual([14, 12, 11]);
    expect(recentInsightsAtCursor(many, 6_000).map((m) => m.id)).toEqual([16, 15, 14]);
    expect(recentInsightsAtCursor(many, 6_000, 0)).toEqual([]);
    expect(recentInsightsAtCursor(many, 1_500).map((m) => m.id)).toEqual([11]);
  });

  it("releases an inspected older actor when playback or the cursor advances", () => {
    expect(selectedAtCursor(timeline, 1, 1_000, false)?.id).toBe(1);
    expect(selectedAtCursor(timeline, 1, 8_000, false)?.id).toBe(4);
    expect(selectedAtCursor(timeline, 1, 8_000, true)?.id).toBe(4);
    expect(selectedAtCursor(timeline, 4, 3_000, false)?.id).toBe(1);
    expect(selectedAtCursor([], 1, 1_000, false)).toBeNull();
  });

  it("does not leak prefetched narratives across cursor, mode, scenario, or replay reset", () => {
    const fact = {
      insight_id: "insight-3",
      audience: "casual" as const,
      headline: "Verified source-only explanation",
      text: "Source event is recorded.",
      source: "local_controlled" as const,
      evidence_event_ids: ["event-2"],
    };
    const scoped = {
      [narrativeStateKey("high_press", "casual", 0, "insight-3")]: fact,
    };
    const find = (
      cursorMs: number,
      scenario = "high_press",
      audience: "casual" | "analyst" | "club" = "casual",
      replayNonce = 0,
    ) => publishedNarrativeAtCursor(
      timeline, cursorMs, scenario, audience, replayNonce, "insight-3", scoped,
    );
    expect(find(4_999)).toBeNull();
    expect(find(5_000)).toEqual(fact);
    expect(find(8_000)).toEqual(fact);
    expect(find(1_000)).toBeNull();
    expect(find(5_000, "counterattack")).toBeNull();
    expect(find(5_000, "high_press", "analyst")).toBeNull();
    expect(find(5_000, "high_press", "casual", 1)).toBeNull();
    expect(publishedNarrativeAtCursor(
      timeline, 5_000, "high_press", "casual", 0, "missing-insight", scoped,
    )).toBeNull();
    const mismatched = {
      [narrativeStateKey("high_press", "casual", 0, "insight-3")]: {
        ...fact,
        audience: "club" as const,
      },
    };
    expect(publishedNarrativeAtCursor(
      timeline, 5_000, "high_press", "casual", 0, "insight-3", mismatched,
    )).toBeNull();
  });

  it("clamps rewind, fast-forward and empty playback bounds", () => {
    expect(matchBounds(timeline)).toEqual({ start: 1_000, end: 8_000 });
    expect(matchBounds([])).toEqual({ start: 0, end: 0 });
    expect(clampCursor(-2_000, 1_000, 8_000)).toBe(1_000);
    expect(clampCursor(10_000, 1_000, 8_000)).toBe(8_000);
    expect(() => clampCursor(Number.NaN, 1_000, 8_000)).toThrow();
  });
});
