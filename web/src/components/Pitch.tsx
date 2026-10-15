import type { MatchEvent } from "../api/types";
import { displayName, eventLabel } from "../domain/presentation";

interface PitchProps {
  event: MatchEvent | null;
}

function pctX(value: number): number {
  return (value / 105) * 100;
}

function pctY(value: number): number {
  return (value / 68) * 100;
}

export function Pitch({ event }: PitchProps) {
  const destination = event?.destination;

  return (
    <section className="panel pitch-panel" aria-label="Interactive football pitch">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Canonical event view</span>
          <h2>105 × 68m pitch</h2>
        </div>
        <span className="status-dot">{event ? event.event_type : "waiting"}</span>
      </div>

      <div className="pitch">
        <svg viewBox="0 0 105 68" role="img" aria-label={event ? eventLabel(event) : "Pitch"}>
          <defs>
            <marker id="arrowhead" markerWidth="4" markerHeight="4" refX="3" refY="2" orient="auto">
              <path d="M0,0 L4,2 L0,4 Z" className="pitch-arrow" />
            </marker>
          </defs>
          <rect x="0.7" y="0.7" width="103.6" height="66.6" rx="1.6" className="pitch-line" />
          <line x1="52.5" y1="0.7" x2="52.5" y2="67.3" className="pitch-line" />
          <circle cx="52.5" cy="34" r="9.15" className="pitch-line" />
          <circle cx="52.5" cy="34" r="0.55" className="pitch-fill" />
          <rect x="0.7" y="13.84" width="16.5" height="40.32" className="pitch-line" />
          <rect x="87.8" y="13.84" width="16.5" height="40.32" className="pitch-line" />
          <rect x="0.7" y="24.84" width="5.5" height="18.32" className="pitch-line" />
          <rect x="98.8" y="24.84" width="5.5" height="18.32" className="pitch-line" />

          {event && destination ? (
            <line
              x1={event.location.x}
              y1={event.location.y}
              x2={destination.x}
              y2={destination.y}
              className="event-path"
              markerEnd="url(#arrowhead)"
            />
          ) : null}
          {event ? (
            <g>
              <circle cx={event.location.x} cy={event.location.y} r="2.1" className="event-pulse" />
              <circle cx={event.location.x} cy={event.location.y} r="1.15" className="event-dot" />
            </g>
          ) : null}
        </svg>

        {event ? (
          <div
            className="pitch-caption"
            style={{
              left: `${Math.min(86, Math.max(6, pctX(event.location.x)))}%`,
              top: `${Math.min(82, Math.max(8, pctY(event.location.y)))}%`,
            }}
          >
            <strong>{event.event_type}</strong>
            <span>{displayName(event.player_id)}</span>
          </div>
        ) : null}
      </div>

      <p className="pitch-note">
        Coordinates and event facts come directly from the canonical synthetic MatchEvent schema.
      </p>
    </section>
  );
}
