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
          <span className="eyebrow">Tactical replay</span>
          <h2>On the pitch</h2>
        </div>
        <span className="status-dot">{event ? event.event_type : "waiting"}</span>
      </div>

      <div className="pitch">
        <svg viewBox="0 0 105 68" role="img" aria-label={event ? eventLabel(event) : "Pitch"}>
          <defs>
            <marker id="arrowhead" markerWidth="4" markerHeight="4" refX="3" refY="2" orient="auto">
              <path d="M0,0 L4,2 L0,4 Z" className="pitch-arrow" />
            </marker>
            <radialGradient id="pv-active-kit" cx="30%" cy="20%" r="75%">
              <stop offset="0%" stopColor="#e3fcff" />
              <stop offset="45%" stopColor="#65c3ea" />
              <stop offset="100%" stopColor="#17709f" />
            </radialGradient>
            <filter id="pv-event-glow" x="-250%" y="-250%" width="600%" height="600%">
              <feGaussianBlur stdDeviation="1.6" />
            </filter>
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
            <g transform={`translate(${event.location.x} ${event.location.y})`}>
              <circle r="4" fill="#b6e64b" opacity=".4" filter="url(#pv-event-glow)" />
              <circle r="3.1" fill="none" stroke="#b6e64b" strokeWidth=".35" />
              <ellipse cx=".65" cy="1.9" rx="1.6" ry=".65" fill="#001b09" opacity=".72" />
              <path
                d="M -0.6 -0.7 L -1.15 1.4 M .55 -.7 L 1.3 1.25"
                stroke="#163849"
                strokeWidth=".65"
                strokeLinecap="round"
              />
              <path
                d="M -1.1 -2.25 L 1 -2.25 L .65 -.5 L -.7 -.5 Z"
                fill="url(#pv-active-kit)"
                stroke="#defaff"
                strokeWidth=".12"
              />
              <path
                d="M -1 -2 L -1.65 -.95 M .95 -2 L 1.6 -1.15"
                stroke="#65c3ea"
                strokeWidth=".5"
                strokeLinecap="round"
              />
              <circle cy="-2.95" r=".63" fill="#f1c9a1" stroke="#5d4231" strokeWidth=".12" />
              <circle cx="1.9" cy="1.1" r=".64" fill="#effff0" stroke="#223329" strokeWidth=".13" />

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
        Event coordinates are source-backed. The highlighted player is a stylized active actor, not
        a reconstructed formation.
      </p>
    </section>
  );
}
