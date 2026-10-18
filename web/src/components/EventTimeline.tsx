import type { ReplayMessage } from "../api/types";
import { isMatchEvent, isTacticalInsight } from "../api/types";
import { clockLabel, displayName } from "../domain/presentation";

interface EventTimelineProps {
  messages: ReplayMessage[];
  selectedId: number | null;
  onSelect: (message: ReplayMessage) => void;
}

export function EventTimeline({ messages, selectedId, onSelect }: EventTimelineProps) {
  return (
    <section className="panel timeline-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Replay</span>
          <h2>Match timeline</h2>
        </div>
        <span className="count-badge">{messages.length}</span>
      </div>

      <section className="timeline" aria-label="Recorded replay events">
        {messages.length === 0 ? (
          <p className="empty-state">Waiting for the deterministic SSE replay…</p>
        ) : (
          messages.map((message) => {
            const selected = selectedId === message.id;
            if (isMatchEvent(message)) {
              const event = message.payload;
              return (
                <button
                  className={`timeline-item ${selected ? "selected" : ""}`}
                  aria-pressed={selected}
                  aria-label={`${event.event_type.replaceAll("_", " ")} at ${clockLabel(event.clock_ms)}, ${displayName(event.team_id)}`}
                  key={message.id}
                  type="button"
                  onClick={() => onSelect(message)}
                >
                  <span className={`event-icon event-${event.event_type}`} />
                  <span className="timeline-copy">
                    <strong>{event.event_type.replaceAll("_", " ")}</strong>
                    <span>
                      {clockLabel(event.clock_ms)} · {displayName(event.team_id)}
                    </span>
                  </span>
                </button>
              );
            }

            if (isTacticalInsight(message)) {
              return (
                <button
                  className={`timeline-item insight-item ${selected ? "selected" : ""}`}
                  aria-pressed={selected}
                  aria-label={`${message.payload.kind.replaceAll("_", " ")} insight at ${clockLabel(message.payload.clock_ms)}`}
                  key={message.id}
                  type="button"
                  onClick={() => onSelect(message)}
                >
                  <span className="event-icon insight-icon" />
                  <span className="timeline-copy">
                    <strong>{message.payload.kind.replaceAll("_", " ")}</strong>
                    <span>{clockLabel(message.payload.clock_ms)} · tactical insight</span>
                  </span>
                </button>
              );
            }
            return null;
          })
        )}
      </section>
    </section>
  );
}
