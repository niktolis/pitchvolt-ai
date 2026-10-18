import type { ReplayMessage } from "../api/types";
import { isMatchEvent, isTacticalInsight } from "../api/types";
import { recentRecordedActions, recordedActionCopy } from "../domain/editorialActivity";
import { clockLabel, displayName } from "../domain/presentation";

interface EventTimelineProps {
  messages: ReplayMessage[];
  selectedId: number | null;
  cursorMs: number;
  onSelect: (message: ReplayMessage) => void;
}

export function EventTimeline({ messages, selectedId, cursorMs, onSelect }: EventTimelineProps) {
  const sourceActivity = recentRecordedActions(messages, cursorMs);
  return (
    <section className="panel timeline-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Replay</span>
          <h2>Match timeline</h2>
        </div>
        <span className="count-badge">{messages.length}</span>
      </div>

      <section className="recorded-action-feed" aria-label="Recorded match activity">
        <div className="recorded-action-heading">
          <strong>Match activity</strong>
          <span>Recorded actions · not tactical insights</span>
        </div>
        {sourceActivity.length ? (
          <div className="recorded-action-items">
            {sourceActivity.map((message) => {
              const copy = recordedActionCopy(message.payload);
              return (
                <button
                  className="recorded-action-item"
                  key={message.payload.event_id}
                  type="button"
                  onClick={() => onSelect(message)}
                  aria-label={`${copy.time}, ${copy.heading}, ${copy.detail}`}
                  title={`Source event ${message.payload.event_id}`}
                >
                  <time dateTime={`PT${message.payload.clock_ms / 1000}S`}>{copy.time}</time>
                  <span className="recorded-action-copy">
                    <strong>{copy.heading}</strong>
                    <small>{copy.detail}</small>
                  </span>
                </button>
              );
            })}
          </div>
        ) : (
          <p className="recorded-action-empty">Waiting for the first recorded action.</p>
        )}
      </section>

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
