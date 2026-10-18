import type { ReplayMessage } from "../api/types";
import { isMatchEvent, isTacticalInsight } from "../api/types";

/** All replay views derive from one authoritative, integer-millisecond cursor. */
export function atOrBefore(messages: readonly ReplayMessage[], cursorMs: number): ReplayMessage[] {
  return messages.filter((item) => item.payload.clock_ms <= cursorMs);
}

export function matchBounds(messages: readonly ReplayMessage[]): { start: number; end: number } {
  if (messages.length === 0) return { start: 0, end: 0 };
  const times = messages.map((item) => item.payload.clock_ms);
  return { start: Math.min(...times), end: Math.max(...times) };
}

export function clampCursor(cursorMs: number, start: number, end: number): number {
  if (!Number.isFinite(cursorMs) || start > end) {
    throw new Error("Invalid replay cursor or match bounds");
  }
  return Math.min(end, Math.max(start, Math.round(cursorMs)));
}

export function latestAtCursor(messages: readonly ReplayMessage[], cursorMs: number) {
  const visible = atOrBefore(messages, cursorMs);
  const selected = visible.at(-1) ?? null;
  const event = [...visible].reverse().find(isMatchEvent)?.payload ?? null;
  const insight = [...visible].reverse().find(isTacticalInsight)?.payload ?? null;
  return { visible, selected, event, insight };
}

/** All narrative updates require a visible insight with the same ID. */
export function visibleNarrativeIds(
  messages: readonly ReplayMessage[],
  cursorMs: number,
): Set<string> {
  return new Set(
    atOrBefore(messages, cursorMs)
      .filter(isTacticalInsight)
      .map((item) => item.payload.insight_id),
  );
}

/** Evidence is never visible before its source insight is published. */
export function isEvidenceVisible(
  messages: readonly ReplayMessage[],
  cursorMs: number,
  insightId: string,
): boolean {
  return visibleNarrativeIds(messages, cursorMs).has(insightId);
}

/** Most recent *published* tactical insights, never inferred from actor movement. */
export function recentInsightsAtCursor(
  messages: readonly ReplayMessage[],
  cursorMs: number,
  limit = 3,
) {
  if (!Number.isFinite(limit) || limit <= 0) return [];
  return atOrBefore(messages, cursorMs)
    .filter(isTacticalInsight)
    .slice(-Math.floor(limit))
    .reverse();
}
