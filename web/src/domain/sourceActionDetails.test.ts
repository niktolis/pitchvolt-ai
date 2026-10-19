import { describe, expect, it } from "vitest";
import type { MatchEvent } from "../api/types";
import { sourceActionDetails } from "./sourceActionDetails";

function action(
  kind: MatchEvent["event_type"],
  overrides: Partial<MatchEvent> = {},
): MatchEvent {
  return {
    match_id: "fictional",
    event_id: "e-42",
    clock_ms: 42_000,
    period: 1,
    sequence: 3,
    observed_at: "2026-01-01T00:00:42Z",
    schema_version: 1,
    event_type: kind,
    player_id: "harbor-8",
    team_id: "harbor",
    possession_team_id: "harbor",
    location: { x: 60, y: 20 },
    destination: { x: 77, y: 18 },
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

function value(details: ReturnType<typeof sourceActionDetails>, label: string): string | undefined {
  return details?.facts.find((fact) => fact.label === label)?.value;
}

describe("source-only Key Moment action details", () => {
  it("reveals a valid carry at source time and distinguishes owner from team", () => {
    const details = sourceActionDetails(action("carry"), 42_000, "Fenwick", "Harbor FC");
    expect(details?.heading).toBe("Recorded carry");
    expect(details?.eventId).toBe("e-42");
    expect(value(details, "Actor")).toBe("Fenwick");
    expect(value(details, "Actor team")).toBe("Harbor FC");
    expect(value(details, "Individual ball holder")).toBe("Fenwick");
    expect(value(details, "Possession team at event")).toBe("Harbor");
    expect(value(details, "Recorded actor location")).toBe("60.0m × 20.0m");
    expect(value(details, "Action destination")).toBe("77.0m × 18.0m");
  });

  it.each(["pass", "shot", "goal", "turnover", "pressure"] as const)(
    "never asserts continued individual control for %s",
    (kind) => {
      const details = sourceActionDetails(action(kind), 42_000, undefined, undefined);
      expect(value(details, "Individual ball holder")).toBe("Not established from this event");
      expect(value(details, "Tracking / contest status")).toBe(
        "No independent ball or opponent tracking",
      );
    },
  );

  it("documents explicit under-pressure evidence without inferring a successful duel", () => {
    const details = sourceActionDetails(
      action("pass", { evidence: { under_pressure: true } }),
      42_000,
      undefined,
      undefined,
    );
    expect(value(details, "Pressure evidence")).toContain("not established");
    expect(value(details, "Individual ball holder")).toContain("Not established");
    expect(details?.qualification).toContain("No tactical conclusion");
  });

  it("does not assign the ball position to a pressing opponent", () => {
    const details = sourceActionDetails(
      action("pressure", {
        player_id: "ridge-4",
        team_id: "ridge",
        possession_team_id: "harbor",
      }),
      42_000,
      undefined,
      undefined,
    );
    expect(value(details, "Ball at action origin")).toBe("Not observed");
    expect(value(details, "Pressing player")).toBe("Ridge 4");
    expect(value(details, "Possession team at event")).toBe("Harbor");
  });

  it("suppresses future events, invalid inputs and invalid coordinate projections", () => {
    expect(sourceActionDetails(action("carry"), 41_999, undefined, undefined)).toBeNull();
    expect(sourceActionDetails(action("carry"), Number.NaN, undefined, undefined)).toBeNull();
    expect(sourceActionDetails(null, 42_000, undefined, undefined)).toBeNull();
    const invalid = sourceActionDetails(
      action("pass", { location: { x: 106, y: 22 }, destination: null }),
      42_000,
      undefined,
      undefined,
    );
    expect(value(invalid, "Recorded actor location")).toBeUndefined();
    expect(value(invalid, "Action destination")).toBeUndefined();
    expect(value(invalid, "Ball at action origin")).toBe("Not observed");
  });
});
