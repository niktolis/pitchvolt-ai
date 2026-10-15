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
