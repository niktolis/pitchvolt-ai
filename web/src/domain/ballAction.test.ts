import { describe, expect, it } from "vitest";
import type { MatchEvent } from "../api/types";
import { ballActionAtCursor } from "./ballAction";

function action(kind: MatchEvent["event_type"], overrides: Partial<MatchEvent> = {}): MatchEvent {
  return {
    match_id: "fictional",
    event_id: "e-23",
    clock_ms: 23_000,
    period: 1,
    sequence: 23,
    observed_at: "2026-01-01T00:00:23Z",
    schema_version: 1,
    event_type: kind,
    player_id: "harbor-8",
    team_id: "harbor",
    possession_team_id: "harbor",
    location: { x: 60, y: 20 },
    outcome: "success",
    provenance: {
      source: "synthetic",
      generator: "test",
      generator_version: "1",
      seed: 0,
      scenario: "fixture",
    },
    ...overrides,
  };
}

describe("honest event-sourced ball and possession presentation", () => {
  it("uses a carry origin as an action-time contact with a known carrier", () => {
    const context = ballActionAtCursor(action("carry"), 23_000);
    expect(context?.location).toEqual({ x: 60, y: 20 });
    expect(context?.carrierId).toBe("harbor-8");
    expect(context?.teamInPossession).toBe("harbor");
    expect(context?.pressured).toBe(false);
  });

  it.each(["pass", "shot", "goal"] as const)(
    "shows the %s action origin but does not assert continuing control",
    (kind) => {
      const context = ballActionAtCursor(action(kind), 23_000);
      expect(context?.location).toEqual({ x: 60, y: 20 });
      expect(context?.initiatedBy).toBe("harbor-8");
      expect(context?.carrierId).toBeNull();
    },
  );

  it("marks an explicitly pressured pass without inventing a duel or a defender location", () => {
    const context = ballActionAtCursor(
      action("pass", {
        evidence: { under_pressure: true },
      }),
      23_000,
    );
    expect(context?.pressured).toBe(true);
    expect(context?.pressingPlayerId).toBeNull();
    expect(context?.location).toEqual({ x: 60, y: 20 });
  });

  it("never draws a ball at a pressing opponent or a turnover", () => {
    const pressure = ballActionAtCursor(
      action("pressure", {
        team_id: "ridge",
        player_id: "ridge-4",
        possession_team_id: "harbor",
      }),
      23_000,
    );
    expect(pressure?.location).toBeNull();
    expect(pressure?.pressingPlayerId).toBe("ridge-4");
    expect(pressure?.carrierId).toBeNull();
    expect(pressure?.teamInPossession).toBe("harbor");
    const turnover = ballActionAtCursor(action("turnover"), 23_000);
    expect(turnover?.location).toBeNull();
    expect(turnover?.carrierId).toBeNull();
  });

  it("never displays a future event's ball or a coordinate outside the pitch", () => {
    expect(ballActionAtCursor(action("carry"), 22_999)).toBeNull();
    expect(ballActionAtCursor(null, 23_000)).toBeNull();
    expect(ballActionAtCursor(action("carry"), Number.NaN)).toBeNull();
    expect(
      ballActionAtCursor(action("carry", { location: { x: 999, y: 0 } }), 23_000)?.location,
    ).toBeNull();
  });

  it("never interprets a pressure event as a current carrier or a ball coordinate", () => {
    const context = ballActionAtCursor(action("pressure"), 23_000);
    expect(context?.initiatedBy).toBeNull();
    expect(context?.carrierId).toBeNull();
    expect(context?.location).toBeNull();
    expect(context?.pressured).toBe(true);
  });
});
