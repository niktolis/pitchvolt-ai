import historicalSource from "../assets/historicalSourceManifest.json";

/** Strict source-observed historical replay contract. No inferred poses or actors. */
export const HISTORICAL_ASSET_PATH = historicalSource.assetPath;
export const HISTORICAL_ASSET_SHA256 = historicalSource.sha256;
export const HISTORICAL_SHOT_FRAME = 12519;
export const HISTORICAL_FIRST_FRAME = 12219;
export const HISTORICAL_FRAME_COUNT = 625;
export const HISTORICAL_FPS = 25;
export const HISTORICAL_LAST_CURSOR_MS = (HISTORICAL_FRAME_COUNT - 1) * 40;

export type SourceTeam = { id: string; name: string; role: "home" | "away" };
export type SourcePlayer = { source_player_id: string; source_team_id: string };
export type SourceFrame = {
  source_frame: number;
  timestamp: string;
  players_xy_m: ([number, number] | null)[];
  ball_xyz_m: [number, number, number];
  source_ball_status: string;
  source_ball_possession_code: string | null;
};
export type HistoricalClip = {
  asset_kind: "source_observed_sportec_clip";
  schema_version: 1;
  public_replay_enabled: false;
  player_carrier_known: false;
  source: {
    license: "CC-BY-4.0";
    original_tracking_sha256: string;
    attribution: string;
    revision: string;
  };
  match: { id: "DFL-MAT-J03WMX"; teams: SourceTeam[]; period: 1 };
  segment: {
    source_event_id: string;
    source_shot_frame: 12519;
    first_frame: 12219;
    last_frame: 12843;
    sample_count: 625;
    frame_rate_hz: 25;
  };
  roster: SourcePlayer[];
  frames: SourceFrame[];
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value);
const validNumber = (value: unknown) => typeof value === "number" && Number.isFinite(value);
const validXY = (v: unknown): v is [number, number] =>
  Array.isArray(v) && v.length === 2 && v.every(validNumber);
const validXYZ = (v: unknown): v is [number, number, number] =>
  Array.isArray(v) && v.length === 3 && v.every(validNumber) && v[2] >= 0;

export function validateHistoricalClip(value: unknown): HistoricalClip {
  if (!isRecord(value)) throw new Error("Invalid original source replay envelope");
  const { source, match, segment, roster, frames } = value;
  if (
    value.asset_kind !== "source_observed_sportec_clip" ||
    value.schema_version !== 1 ||
    value.public_replay_enabled !== false ||
    value.player_carrier_known !== false ||
    !isRecord(source) ||
    source.license !== "CC-BY-4.0" ||
    source.original_tracking_sha256 !== historicalSource.originalTrackingSha256 ||
    typeof source.attribution !== "string" ||
    !source.attribution.includes("Deutsche Fußball Liga") ||
    !isRecord(match) ||
    match.id !== historicalSource.matchId ||
    match.period !== 1 ||
    !Array.isArray(match.teams) ||
    match.teams.length !== 2 ||
    !match.teams.every(
      (team) =>
        isRecord(team) &&
        typeof team.id === "string" &&
        typeof team.name === "string" &&
        (team.role === "home" || team.role === "away"),
    ) ||
    !isRecord(segment) ||
    segment.source_event_id !== historicalSource.sourceEventId ||
    segment.source_shot_frame !== HISTORICAL_SHOT_FRAME ||
    segment.first_frame !== HISTORICAL_FIRST_FRAME ||
    segment.last_frame !== 12843 ||
    segment.sample_count !== HISTORICAL_FRAME_COUNT ||
    segment.frame_rate_hz !== HISTORICAL_FPS ||
    !Array.isArray(roster) ||
    roster.length !== 22 ||
    !Array.isArray(frames) ||
    frames.length !== HISTORICAL_FRAME_COUNT
  ) {
    throw new Error("Historical replay does not match the pinned original match");
  }

  const players = roster as SourcePlayer[];
  const teams = new Set((match.teams as SourceTeam[]).map((team) => team.id));
  if (
    teams.size !== 2 ||
    new Set(players.map((player) => player.source_player_id)).size !== 22 ||
    players.some(
      (player) =>
        !isRecord(player) ||
        typeof player.source_player_id !== "string" ||
        !teams.has(player.source_team_id),
    )
  ) {
    throw new Error("Missing or ambiguous observed footballer identity");
  }

  const firstTimestamp = Date.parse((frames[0] as SourceFrame).timestamp);
  if (!Number.isFinite(firstTimestamp)) {
    throw new Error("Original frame clock is missing");
  }
  for (let index = 0; index < HISTORICAL_FRAME_COUNT; index += 1) {
    const frame: unknown = frames[index];
    if (
      !isRecord(frame) ||
      frame.source_frame !== HISTORICAL_FIRST_FRAME + index ||
      typeof frame.timestamp !== "string" ||
      !Number.isFinite(Date.parse(frame.timestamp)) ||
      Math.abs(Date.parse(frame.timestamp) - firstTimestamp - 40 * index) > 2 ||
      !Array.isArray(frame.players_xy_m) ||
      frame.players_xy_m.length !== 22 ||
      !frame.players_xy_m.every(validXY) ||
      !validXYZ(frame.ball_xyz_m)
    ) {
      throw new Error(`Unverified or missing source observation at sample ${index}`);
    }
    const counted = new Map<string, number>();
    for (let p = 0; p < players.length; p += 1) {
      if (!validXY(frame.players_xy_m[p])) {
        throw new Error("Unobserved historical footballer cannot be displayed");
      }
      const id = players[p]?.source_team_id ?? "";
      counted.set(id, (counted.get(id) ?? 0) + 1);
    }
    if ([...counted.values()].sort((a, b) => a - b).join(",") !== "11,11") {
      throw new Error("Original frame lacks 11 per team");
    }
  }
  return value as HistoricalClip;
}

/** Source-exact 25 Hz cursor: sample 0..624; never invent an intermediate pose. */
export function exactFrameAtCursor(clip: HistoricalClip, elapsedMs: number): SourceFrame {
  const bounded = Math.max(0, Math.min(HISTORICAL_LAST_CURSOR_MS, elapsedMs));
  const index = Math.floor(bounded / 40);
  const result = clip.frames[index];
  if (!result || result.source_frame !== HISTORICAL_FIRST_FRAME + index) {
    throw new Error("Observed frame unavailable; refusing nearest replacement");
  }
  return result;
}

export async function loadHistoricalClip(
  fetcher: typeof fetch = fetch,
  verifyDigest = true,
): Promise<HistoricalClip> {
  const response = await fetcher(HISTORICAL_ASSET_PATH, { cache: "force-cache" });
  if (!response.ok) throw new Error("Verified historical match asset is unavailable");
  const data = await response.arrayBuffer();
  if (verifyDigest) {
    if (!globalThis.crypto?.subtle) {
      throw new Error("Web Crypto checksum validation unavailable");
    }
    const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", data)))
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("");
    if (hash !== HISTORICAL_ASSET_SHA256) {
      throw new Error("Historical source replay SHA-256 failed verification");
    }
  }
  const parsed: unknown = JSON.parse(new TextDecoder().decode(data));
  return validateHistoricalClip(parsed);
}
