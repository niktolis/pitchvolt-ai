import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

const manifest = JSON.parse(
  readFileSync(new URL("../src/assets/historicalSourceManifest.json", import.meta.url), "utf8"),
);
const production = process.argv.includes("--dist");
const location = production
  ? new URL("../dist/historical/j03wmx-shot-12519-observed-v1.json", import.meta.url)
  : new URL("../public/historical/j03wmx-shot-12519-observed-v1.json", import.meta.url);

const bytes = readFileSync(location);
assert.equal(bytes.length, 381441, "Pinned historical source asset byte length differs");
assert.equal(
  createHash("sha256").update(bytes).digest("hex"),
  manifest.sha256,
  "Historical replay asset differs from its verified digest",
);
const data = JSON.parse(bytes.toString("utf8"));
assert.equal(data.asset_kind, "source_observed_sportec_clip");
assert.equal(data.public_replay_enabled, false);
assert.equal(data.player_carrier_known, false);
assert.equal(data.source.license, "CC-BY-4.0");
assert.match(data.source.attribution, /Deutsche Fußball Liga/);
assert.equal(data.source.original_tracking_sha256, manifest.originalTrackingSha256);
assert.equal(data.match.id, manifest.matchId);
assert.equal(data.segment.source_event_id, manifest.sourceEventId);
assert.equal(data.segment.first_frame, manifest.firstFrame);
assert.equal(data.segment.last_frame, manifest.lastFrame);
assert.equal(data.segment.frame_rate_hz, manifest.frameRate);
assert.equal(data.segment.sample_count, manifest.frameCount);
assert.equal(data.roster.length, 22);
assert.equal(new Set(data.roster.map((p) => p.source_player_id)).size, 22);
assert.equal(data.frames.length, manifest.frameCount);
for (const [i, frame] of data.frames.entries()) {
  assert.equal(frame.source_frame, manifest.firstFrame + i);
  assert.equal(frame.players_xy_m.length, 22);
  assert.ok(frame.players_xy_m.every((point) =>
    Array.isArray(point) && point.length === 2 && point.every(Number.isFinite)
  ), "Cannot replace a source-observed player with a synthetic pose");
  assert.ok(
    Array.isArray(frame.ball_xyz_m) &&
      frame.ball_xyz_m.length === 3 &&
      frame.ball_xyz_m.every(Number.isFinite) &&
      frame.ball_xyz_m[2] >= 0,
    "Recorded ball XYZ must exist for every source frame",
  );
}
console.log(
  `IDSSE ${production ? "production" : "source"} asset accepted: ${manifest.sha256}, ${data.frames.length} exact frames`,
);
