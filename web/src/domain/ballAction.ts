import type { MatchEvent } from "../api/types";
import { isSourcePitchPoint } from "../components/pitch-geometry";

/**
 * Event-contact marker, NOT a physical ball-tracking observation.
 * Source actions identify a point at which the actor played/carried the ball.
 * No ball is positioned for pressure or possession-changing turnover events.
 */
export interface BallActionContext {
  eventId: string;
  clockMs: number;
  teamInPossession: string;
  pressingPlayerId: string | null;
  initiatedBy: string | null;
  carrierId: string | null;
  actionKind: MatchEvent["event_type"];
  pressured: boolean;
  location: MatchEvent["location"] | null;
}

export function ballActionAtCursor(
  event: MatchEvent | null,
  cursorMs: number,
): BallActionContext | null {
  if (!event || !Number.isFinite(cursorMs) || event.clock_ms > cursorMs) return null;

  const touchedBall = ["pass", "carry", "shot", "goal"].includes(event.event_type);
  const validActionOrigin = touchedBall && isSourcePitchPoint(event.location);
  const teamControls = event.possession_team_id === event.team_id;

  return {
    eventId: event.event_id,
    clockMs: event.clock_ms,
    teamInPossession: event.possession_team_id,
    pressingPlayerId: event.event_type === "pressure" ? event.player_id : null,
    // A passer/shooter initiated this action; this does NOT identify a current ball holder.
    initiatedBy: validActionOrigin ? event.player_id : null,
    // Only a recorded carry supports ball control by the actor at its starting timestamp.
    carrierId:
      validActionOrigin && event.event_type === "carry" && teamControls ? event.player_id : null,
    actionKind: event.event_type,
    // Source "under_pressure" is pressure evidence, NOT proof of a 50/50 duel.
    pressured: event.evidence?.under_pressure === true || event.event_type === "pressure",
    location: validActionOrigin ? event.location : null,
  };
}
