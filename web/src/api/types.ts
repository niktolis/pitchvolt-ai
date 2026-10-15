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
