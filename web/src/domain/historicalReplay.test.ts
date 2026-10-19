import { describe, expect, it } from "vitest";
import {
  exactFrameAtCursor,
  HISTORICAL_ASSET_PATH,
  HISTORICAL_FIRST_FRAME,
  HISTORICAL_FRAME_COUNT,
  HISTORICAL_SHOT_FRAME,
  loadHistoricalClip,
  validateHistoricalClip,
} from "./historicalReplay";

function syntheticContract() {
  const teams = [
    { id: "verified-home-id", name: "Home (TEST)", role: "home" },
    { id: "verified-away-id", name: "Away (TEST)", role: "away" },
  ];
  const roster = Array.from({ length: 22 }, (_, i) => ({
    source_player_id: `authored-test-${i}`,
    source_team_id: teams[i < 11 ? 0 : 1].id,
  }));
  const original = Date.parse("2023-05-27T13:31:41.360+00:00");
  const frames = Array.from({ length: HISTORICAL_FRAME_COUNT }, (_, i) => ({
    source_frame: HISTORICAL_FIRST_FRAME + i,
    timestamp: new Date(original + i * 40).toISOString(),
    players_xy_m: Array.from({ length: 22 }, (_, j) => [j + i * 0.01, (j % 11) + 8]),
    ball_xyz_m: [40 + i * 0.01, 30, i === 300 ? 4.2 : 0.2],
    source_ball_status: "1",
    source_ball_possession_code: "2",
  }));
  return {
    asset_kind: "source_observed_sportec_clip",
    schema_version: 1,
    source: {
      license: "CC-BY-4.0",
      original_tracking_sha256: "d3dd92e509421a6466acb0a083c009035f1751bc5fd9ef42ffa8f20d01cf7d49",
      attribution: "Deutsche Fußball Liga · TEST ORIGINAL FICTION",
      revision: "pinned-authored-test",
    },
    match: { id: "DFL-MAT-J03WMX", teams, period: 1 },
    segment: {
      source_event_id: "18226500000041",
      source_shot_frame: HISTORICAL_SHOT_FRAME,
      first_frame: HISTORICAL_FIRST_FRAME,
      last_frame: 12843,
      sample_count: 625,
      frame_rate_hz: 25,
    },
    roster,
    frames,
    player_carrier_known: false,
    public_replay_enabled: false,
  };
}

describe("IDSSE historical replay source-only semantics", () => {
  it("accepts exact 625-frame source-shaped data and seeks without interpolation", () => {
    const clip = validateHistoricalClip(syntheticContract());
    expect(clip.frames).toHaveLength(625);
    expect(exactFrameAtCursor(clip, 0).source_frame).toBe(12219);
    expect(exactFrameAtCursor(clip, 12_000).source_frame).toBe(12519);
    expect(exactFrameAtCursor(clip, 24_960).source_frame).toBe(12843);
    expect(exactFrameAtCursor(clip, 12_039).source_frame).toBe(12519);
    expect(exactFrameAtCursor(clip, 12_040).source_frame).toBe(12520);
    expect(exactFrameAtCursor(clip, -100).source_frame).toBe(12219);
    expect(exactFrameAtCursor(clip, 10_000_000).source_frame).toBe(12843);
    expect(exactFrameAtCursor(clip, 12_000).ball_xyz_m[2]).toBe(4.2);
  });

  it("refuses missing players, fabricated in-between frames and wrong IDs", () => {
    for (const mutate of [
      (raw: ReturnType<typeof syntheticContract>) => {
        raw.frames[7].players_xy_m.pop();
      },
      (raw: ReturnType<typeof syntheticContract>) => {
        raw.frames[22].source_frame += 1;
      },
      (raw: ReturnType<typeof syntheticContract>) => {
        raw.frames[27].timestamp = raw.frames[26].timestamp;
      },
      (raw: ReturnType<typeof syntheticContract>) => {
        raw.frames[40].ball_xyz_m[2] = Number.NaN;
      },
      (raw: ReturnType<typeof syntheticContract>) => {
        raw.roster[1].source_player_id = raw.roster[0].source_player_id;
      },
      (raw: ReturnType<typeof syntheticContract>) => {
        raw.public_replay_enabled = true;
      },
    ]) {
      const bad = syntheticContract();
      mutate(bad);
      expect(() => validateHistoricalClip(bad)).toThrow();
    }
  });

  it("loads only same-origin reviewed file and fails closed on absent data", async () => {
    expect(HISTORICAL_ASSET_PATH).toBe("/historical/j03wmx-shot-12519-observed-v1.json");
    const errorFetcher = async () => new Response("", { status: 404 });
    await expect(loadHistoricalClip(errorFetcher as typeof fetch, false)).rejects.toThrow(
      "unavailable",
    );
    const fakeFetcher = async () => new Response(JSON.stringify(syntheticContract()));
    const loaded = await loadHistoricalClip(fakeFetcher as typeof fetch, false);
    expect(loaded.frames).toHaveLength(625);
  });
});
