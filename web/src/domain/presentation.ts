import type { MatchEvent, TacticalInsight } from "../api/types";

export type AudienceMode = "casual" | "analyst" | "club";

export interface InsightFacts {
  transitionSeconds: number;
  attackingActions: number;
  evidenceCount: number;
  team: string;
  kind: string;
}

function metric(insight: TacticalInsight, key: string): number {
  const value = insight.metrics[key];
  return typeof value === "number" ? value : 0;
}

export function displayName(identifier: string): string {
  return identifier
    .split("-")
    .map((part) =>
      part.toLowerCase() === "fc" ? "FC" : part.charAt(0).toUpperCase() + part.slice(1),
    )
    .join(" ");
}

export function clockLabel(clockMs: number): string {
  const totalSeconds = Math.floor(clockMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export function insightFacts(insight: TacticalInsight): InsightFacts {
  return {
    transitionSeconds: metric(insight, "transition_duration_ms") / 1000,
    attackingActions: metric(insight, "attacking_actions"),
    evidenceCount: insight.evidence_event_ids.length,
    team: displayName(insight.team_id),
    kind: insight.kind.replaceAll("_", " "),
  };
}

export function modeCopy(mode: AudienceMode, insight: TacticalInsight): string {
  if (insight.kind === "sustained_possession") {
    const team = displayName(insight.team_id);
    const duration = insight.metrics.sequence_duration_ms;
    const passes = insight.metrics.passes;
    const time = typeof duration === "number" ? `${(duration / 1000).toFixed(1)}s` : "unknown duration";
    const count = typeof passes === "number" ? `${passes} recorded passes` : "passes not quantified";
    if (mode === "analyst") {
      return `Sustained possession · ${time} · ${count} · ${insight.evidence_event_ids.length} evidence events`;
    }
    if (mode === "club") {
      return `${team} maintained possession over ${time} with ${count}.`;
    }
    return `${team} maintained possession for ${time} with ${count}.`;
  }
  const facts = insightFacts(insight);
  const seconds = facts.transitionSeconds.toFixed(1);

  if (mode === "analyst") {
    return `${facts.kind} · ${seconds}s transition · ${facts.attackingActions} attacking actions · ${facts.evidenceCount} evidence events`;
  }
  if (mode === "club") {
    return `${facts.team} converted the regain into a shot in ${seconds}s across ${facts.attackingActions} attacking actions.`;
  }
  return `${facts.team} turned a ball recovery into a shot in ${seconds}s.`;
}

export function eventLabel(event: MatchEvent): string {
  const eventType = event.event_type.replaceAll("_", " ");
  return `${clockLabel(event.clock_ms)} · ${displayName(event.team_id)} · ${eventType}`;
}
