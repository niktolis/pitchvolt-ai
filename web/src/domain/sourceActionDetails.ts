import type { MatchEvent } from "../api/types";
import { ballActionAtCursor } from "./ballAction";
import { clockLabel, displayName } from "./presentation";
import { isSourcePitchPoint } from "../components/pitch-geometry";

export interface SourceActionFact {
  label: string;
  value: string;
}

export interface SourceActionDetails {
  eventId: string;
  heading: string;
  facts: SourceActionFact[];
  qualification: string;
}

/**
 * Display only fields recorded by the replay source, never inferred tactics.
 * Historical source fixtures and synthetic fixtures must remain distinguishable.
 */
export function sourceActionDetails(
  event: MatchEvent | null,
  cursorMs: number,
  actorLabel: string | undefined,
  teamLabel: string | undefined,
): SourceActionDetails | null {
  if (!event || !Number.isFinite(cursorMs) || event.clock_ms > cursorMs) return null;

  const ball = ballActionAtCursor(event, cursorMs);
  const facts: SourceActionFact[] = [
    { label: "Event time", value: clockLabel(event.clock_ms) },
    { label: "Recorded action", value: event.event_type.replaceAll("_", " ") },
    { label: "Actor", value: actorLabel ?? displayName(event.player_id) },
    { label: "Actor team", value: teamLabel ?? displayName(event.team_id) },
    { label: "Recorded outcome", value: event.outcome },
    { label: "Possession team at event", value: displayName(event.possession_team_id) },
  ];

  if (isSourcePitchPoint(event.location)) {
    facts.push({
      label: "Recorded actor location",
      value: `${event.location.x.toFixed(1)}m × ${event.location.y.toFixed(1)}m`,
    });
  }
  if (isSourcePitchPoint(event.destination)) {
    facts.push({
      label: "Action destination",
      value: `${event.destination.x.toFixed(1)}m × ${event.destination.y.toFixed(1)}m`,
    });
  }

  facts.push({
    label: "Ball at action origin",
    value: ball?.location ? "Event-contact marker (not tracked)" : "Not observed",
  });
  facts.push({
    label: "Individual ball holder",
    value: ball?.carrierId
      ? actorLabel ?? displayName(ball.carrierId)
      : "Not established from this event",
  });
  if (ball?.pressingPlayerId) {
    facts.push({
      label: "Pressing player",
      value: actorLabel ?? displayName(ball.pressingPlayerId),
    });
  }
  if (ball?.pressured) {
    facts.push({ label: "Pressure evidence", value: "Reported; a contested ball is not established" });
  }
  facts.push({
    label: "Tracking / contest status",
    value: "No independent ball or opponent tracking",
  });

  return {
    eventId: event.event_id,
    heading: `Recorded ${event.event_type.replaceAll("_", " ")}`,
    facts,
    qualification: "Source-authored event facts only. No tactical conclusion or ball trajectory is inferred.",
  };
}
