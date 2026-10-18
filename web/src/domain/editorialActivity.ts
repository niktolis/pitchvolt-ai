import type { MatchEvent, ReplayMessage } from "../api/types";
import { isMatchEvent } from "../api/types";
import { clockLabel, displayName } from "./presentation";
import { atOrBefore } from "./replayClock";

/**
 * Recent *recorded* actions at the one replay cursor.
 *
 * Insight, narrative, and substitution presentation messages are not action
 * records; do not pad activity with implied tackles, goals, probabilities, or
 * unverified interpretation. This projection never produces player positions.
 */
export function recentRecordedActions(
  messages: readonly ReplayMessage[],
  cursorMs: number,
  limit = 3,
): Array<ReplayMessage & { kind: "match_event"; payload: MatchEvent }> {
  if (!Number.isFinite(cursorMs) || !Number.isFinite(limit) || limit <= 0) return [];
  return atOrBefore(messages, cursorMs).filter(isMatchEvent).slice(-Math.floor(limit)).reverse();
}

/** Readable play-by-play from source fields only; no inferred success or score. */
export function recordedActionCopy(event: MatchEvent): {
  heading: string;
  detail: string;
  time: string;
} {
  const action = event.event_type.replaceAll("_", " ");
  const team = displayName(event.team_id);
  const result = event.outcome === "neutral" ? "Recorded action" : `Recorded ${event.outcome}`;
  return {
    heading: `${team} · ${action}`,
    detail: result,
    time: clockLabel(event.clock_ms),
  };
}
