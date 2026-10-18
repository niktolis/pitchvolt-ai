import { describe, expect, it } from "vitest";

import type { MatchPresentation } from "../api/types";
import {
  lineupAtCursor,
  playerLabel,
  scoreAtCursor,
  teamLabel,
} from "./fixturePresentation";

const known: MatchPresentation = {
  match_id: "fictional-fixture",
  source: "authored_fictional",
  coverage: "full_match",
  initial_score_known: true,
  home: {
    team_id: "harbor-fc",
    name: "Harbor FC",
    abbreviation: "HFC",
    primary_color: "#47b5db",
    secondary_color: "#0c3852",
    emblem_text: "HFC",
    coach: "Mira Vale",
    players: [
      { player_id: "harbor-1", surname: "Marlow", jersey_number: 1 },
      { player_id: "harbor-12", surname: "Wren", jersey_number: 12 },
    ],
    starters: ["harbor-1"],
  },
  away: {
    team_id: "ridge-fc",
    name: "Ridge FC",
    abbreviation: "RFC",
    primary_color: "#ed765b",
    secondary_color: "#642a31",
    emblem_text: "RFC",
    coach: "Elias North",
    players: [{ player_id: "ridge-1", surname: "North", jersey_number: 1 }],
    starters: ["ridge-1"],
  },
  goals: [
    { event_id: "goal-1", period: 2, clock_ms: 3_500_000, home: 1, away: 0 },
  ],
  substitutions: [{
    event_id: "sub-1",
    clock_ms: 3_660_000,
    period: 2,
    team_id: "harbor-fc",
    outgoing_player_id: "harbor-1",
    incoming_player_id: "harbor-12",
  }],
  lineup_samples: [{
    event_id: "sub-1",
    clock_ms: 3_660_000,
    home_active: ["harbor-12"],
    away_active: ["ridge-1"],
  }],
};

describe("backend-authored replay presentation", () => {
  it("derives score exclusively from known kickoff and explicit goal samples", () => {
    expect(scoreAtCursor(known, 0)).toEqual({ home: 0, away: 0 });
    expect(scoreAtCursor(known, 3_499_999)).toEqual({ home: 0, away: 0 });
    expect(scoreAtCursor(known, 3_500_000)).toEqual({ home: 1, away: 0 });
    expect(scoreAtCursor(known, 5_400_000)).toEqual({ home: 1, away: 0 });
    expect(scoreAtCursor(known, 3_400_000)).toEqual({ home: 0, away: 0 });
  });

  it("never turns an unknown second-half excerpt into 0:0", () => {
    const excerpt: MatchPresentation = {
      ...known,
      coverage: "excerpt",
      initial_score_known: false,
      goals: [],
      home: { ...known.home, starters: null },
      away: { ...known.away, starters: null },
      substitutions: [],
      lineup_samples: [],
    };
    expect(scoreAtCursor(excerpt, 3_800_000)).toBeNull();
    expect(lineupAtCursor(excerpt, 3_800_000)).toBeNull();
    expect(scoreAtCursor(null, 10)).toBeNull();
  });

  it("rewinds lineup changes to their source-authored event time", () => {
    expect(lineupAtCursor(known, 3_659_999)?.home_active).toEqual(["harbor-1"]);
    expect(lineupAtCursor(known, 3_660_000)?.home_active).toEqual(["harbor-12"]);
    expect(lineupAtCursor(known, 5_400_000)?.away_active).toEqual(["ridge-1"]);
    expect(lineupAtCursor(known, 2_000)?.home_active).toEqual(["harbor-1"]);
  });

  it("uses explicitly authored surnames, never infers from player IDs", () => {
    expect(playerLabel(known, "harbor-12")).toBe("Wren");
    expect(playerLabel(known, "unknown-player")).toBe("unknown-player");
    expect(teamLabel(known, "ridge-fc")).toBe("Ridge FC");
    expect(teamLabel(known, "unknown-team")).toBe("unknown-team");
  });
});
