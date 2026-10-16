import type { components } from "./generated";

export type MatchEvent = components["schemas"]["MatchEvent"];
export type ReplayMessage = components["schemas"]["ReplayMessage"];
export type TacticalInsight = components["schemas"]["TacticalInsightPayload"];
export type EvidenceResponse = components["schemas"]["EvidenceResponse"];
export type ScenarioCatalog = components["schemas"]["ScenarioCatalog"];

export function isMatchEvent(
  message: ReplayMessage,
): message is ReplayMessage & { kind: "match_event"; payload: MatchEvent } {
  return message.kind === "match_event";
}

export function isTacticalInsight(message: ReplayMessage): message is ReplayMessage & {
  kind: "tactical_insight";
  payload: TacticalInsight;
} {
  return message.kind === "tactical_insight";
}

// The narrative SSE contract is provisional and intentionally not part of the
// existing immutable replay-publication schema. It uses validated server fields.
export interface NarrativeUpdate {
  insight_id: string;
  audience: "casual" | "analyst" | "club";
  headline: string;
  text: string;
  source: "local_controlled" | "deterministic_fallback";
  evidence_event_ids: string[];
}
