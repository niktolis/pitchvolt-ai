import type { MatchEvent } from "../api/types";
import { displayName } from "../domain/presentation";
import { isSourcePitchPoint } from "./pitch-geometry";

export function SourceMomentPreview({ event }: { event: MatchEvent | null }) {
  const actor = event?.player_id.trim() && isSourcePitchPoint(event.location) ? event : null;
  const destination = actor && isSourcePitchPoint(actor.destination) ? actor.destination : null;

  return (
    <div className="key-moment-scene key-moment-source-scene">
      <svg
        viewBox="0 0 105 68"
        role="img"
        aria-label={
          actor
            ? `Recorded event position for ${displayName(actor.player_id)} on the pitch`
            : "Key moment location unavailable"
        }
      >
        <defs>
          <marker
            id="moment-destination-tip"
            markerWidth="4"
            markerHeight="4"
            refX="4"
            refY="2"
            orient="auto"
          >
            <path d="M 0 0 L 4 2 L 0 4 Z" fill="#b6e64b" />
          </marker>
        </defs>
        <rect
          x="0.7"
          y="0.7"
          width="103.6"
          height="66.6"
          rx="1"
          fill="none"
          stroke="#d8eed2"
          strokeWidth=".45"
        />
        <line x1="52.5" y1="0.7" x2="52.5" y2="67.3" stroke="#d8eed2" strokeWidth=".4" />
        <circle cx="52.5" cy="34" r="9.15" fill="none" stroke="#d8eed2" strokeWidth=".4" />
        <rect
          x="0.7"
          y="13.84"
          width="16.5"
          height="40.32"
          fill="none"
          stroke="#d8eed2"
          strokeWidth=".4"
        />
        <rect
          x="87.8"
          y="13.84"
          width="16.5"
          height="40.32"
          fill="none"
          stroke="#d8eed2"
          strokeWidth=".4"
        />
        {actor && destination ? (
          <line
            x1={actor.location.x}
            y1={actor.location.y}
            x2={destination.x}
            y2={destination.y}
            stroke="#b6e64b"
            strokeWidth=".85"
            markerEnd="url(#moment-destination-tip)"
          />
        ) : null}
        {actor ? (
          <g transform={`translate(${actor.location.x} ${actor.location.y})`}>
            <circle r="4.2" fill="#b6e64b" fillOpacity=".2" />
            <circle r="2.5" fill="none" stroke="#b6e64b" strokeWidth=".7" />
            <circle r=".9" fill="#e9ffe0" />
          </g>
        ) : null}
      </svg>
      <span className="moment-provenance-label">
        {actor ? "Recorded event actor" : "No source position"}
      </span>
    </div>
  );
}
