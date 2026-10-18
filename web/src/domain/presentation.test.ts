import { describe, expect, it } from "vitest";

import type { TacticalInsight } from "../api/types";
import { insightFacts, modeCopy } from "./presentation";

const insight: TacticalInsight = {
  insight_id: "synthetic-e006:high_press",
  kind: "high_press",
  team_id: "harbor-fc",
  clock_ms: 4_050_000,
  evidence_event_ids: ["e1", "e2", "e3", "e4", "e5", "e6"],
  metrics: {
    transition_duration_ms: 10_500,
    attacking_actions: 4,
  },
};

describe("audience presentation", () => {
  it("does not invent a shot or transition for recorded sustained possession", () => {
    const possession: TacticalInsight = {
      ...insight,
      insight_id: "synthetic-p015:sustained_possession",
      kind: "sustained_possession",
      metrics: { sequence_duration_ms: 18000, passes: 7 },
    };
    for (const mode of ["casual", "analyst", "club"] as const) {
      const copy = modeCopy(mode, possession).toLowerCase();
      expect(copy).toContain("18.0");
      expect(copy).toContain("7 recorded passes");
      expect(copy).not.toContain("shot");
      expect(copy).not.toContain("regain");
      expect(copy).not.toContain("transition");
    }
  });

  it("keeps one factual payload across every audience mode", () => {
    expect(insightFacts(insight)).toEqual({
      transitionSeconds: 10.5,
      attackingActions: 4,
      evidenceCount: 6,
      team: "Harbor FC",
      kind: "high press",
    });

    for (const mode of ["casual", "analyst", "club"] as const) {
      expect(modeCopy(mode, insight)).toContain("10.5");
    }
  });
});
