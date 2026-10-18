import type { MatchPresentation } from "../api/types";

/** Server-authored score transitions, never re-derived from UI action guesses. */
export function scoreAtCursor(
  profile: MatchPresentation | null,
  cursorMs: number,
): { home: number; away: number } | null {
  if (!profile?.initial_score_known) return null;
  const state = profile.goals.filter((item) => item.clock_ms <= cursorMs).at(-1);
  return state ? { home: state.home, away: state.away } : { home: 0, away: 0 };
}

/** Read source-authored active roster snapshots, never positions or formations. */
export function lineupAtCursor(
  profile: MatchPresentation | null,
  cursorMs: number,
): { home_active: string[]; away_active: string[] } | null {
  if (!profile?.home.starters || !profile.away.starters) return null;
  const last = profile.lineup_samples.filter((item) => item.clock_ms <= cursorMs).at(-1);
  return last
    ? { home_active: last.home_active, away_active: last.away_active }
    : { home_active: profile.home.starters, away_active: profile.away.starters };
}

export function playerLabel(profile: MatchPresentation | null, playerId: string): string {
  const player = [...(profile?.home.players ?? []), ...(profile?.away.players ?? [])].find(
    (item) => item.player_id === playerId,
  );
  return player?.surname ?? playerId;
}

export function teamLabel(profile: MatchPresentation | null, teamId: string): string {
  return [profile?.home, profile?.away].find((item) => item?.team_id === teamId)?.name ?? teamId;
}
