import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchEvidence, fetchScenarios, openNarrativeStream, openReplayStream } from "./api/client";
import type {
  EvidenceResponse,
  MatchEvent,
  NarrativeUpdate,
  ReplayMessage,
  TacticalInsight,
} from "./api/types";
import { isMatchEvent, isTacticalInsight } from "./api/types";
import { EventTimeline } from "./components/EventTimeline";
import { Pitch } from "./components/Pitch";
import {
  type AudienceMode,
  clockLabel,
  displayName,
  eventLabel,
  modeCopy,
} from "./domain/presentation";

const SPEEDS = [1, 5, 25] as const;
const MODES: AudienceMode[] = ["casual", "analyst", "club"];

export function App() {
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [scenario, setScenario] = useState("");
  const [speed, setSpeed] = useState<number>(5);
  const [mode, setMode] = useState<AudienceMode>("casual");
  const [messages, setMessages] = useState<ReplayMessage[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [narratives, setNarratives] = useState<Record<string, NarrativeUpdate>>({});
  const [narrativeError, setNarrativeError] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<EvidenceResponse | null>(null);
  const [streamState, setStreamState] = useState<"connecting" | "live" | "complete" | "error">(
    "connecting",
  );
  const [error, setError] = useState<string | null>(null);
  const [replayNonce, setReplayNonce] = useState(0);

  useEffect(() => {
    let active = true;
    fetchScenarios()
      .then((items) => {
        if (!active) return;
        setScenarios(items);
        setScenario((current) => current || items[0] || "");
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setError(reason instanceof Error ? reason.message : "Unable to load scenarios.");
        setStreamState("error");
      });
    return () => {
      active = false;
    };
  }, []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: replayNonce intentionally restarts the finite EventSource replay.
  useEffect(() => {
    if (!scenario) return undefined;

    setMessages([]);
    setSelectedId(null);
    setEvidence(null);
    setError(null);
    setStreamState("connecting");

    return openReplayStream(scenario, speed, {
      onMessage: (message) => {
        setMessages((current) => [...current, message]);
        setSelectedId(message.id);
        setStreamState("live");
      },
      onComplete: () => setStreamState("complete"),
      onError: (message) => {
        setError(message);
        setStreamState("error");
      },
    });
  }, [scenario, speed, replayNonce]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: replayNonce intentionally restarts the narrative replay together with the match replay.
  useEffect(() => {
    if (!scenario) return undefined;
    setNarratives({});
    setNarrativeError(null);
    let active = true;
    const close = openNarrativeStream(scenario, mode, {
      onNarrative: (message) => {
        if (active) {
          setNarratives((current) => ({ ...current, [message.insight_id]: message }));
        }
      },
      onError: (message) => {
        if (active) setNarrativeError(message);
      },
    });
    return () => {
      active = false;
      close();
    };
  }, [scenario, mode, replayNonce]);

  const selected = useMemo(
    () => messages.find((message) => message.id === selectedId) ?? messages.at(-1) ?? null,
    [messages, selectedId],
  );

  const latestInsight = useMemo(() => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const candidate = messages[index];
      if (candidate && isTacticalInsight(candidate)) return candidate.payload;
    }
    return null;
  }, [messages]);

  const selectedEvent = useMemo<MatchEvent | null>(() => {
    if (selected && isMatchEvent(selected)) return selected.payload;
    if (selected && isTacticalInsight(selected)) {
      const ids = new Set(selected.payload.evidence_event_ids);
      for (let index = messages.length - 1; index >= 0; index -= 1) {
        const candidate = messages[index];
        if (candidate && isMatchEvent(candidate) && ids.has(candidate.payload.event_id)) {
          return candidate.payload;
        }
      }
    }
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const candidate = messages[index];
      if (candidate && isMatchEvent(candidate)) return candidate.payload;
    }
    return null;
  }, [messages, selected]);

  const inspect = useCallback(
    async (message: ReplayMessage) => {
      setSelectedId(message.id);
      if (!isTacticalInsight(message) || !scenario) {
        setEvidence(null);
        return;
      }
      try {
        setEvidence(await fetchEvidence(scenario, message.payload.insight_id));
      } catch (reason: unknown) {
        setError(reason instanceof Error ? reason.message : "Unable to load evidence.");
      }
    },
    [scenario],
  );

  const matchClock = selectedEvent?.clock_ms ?? latestInsight?.clock_ms ?? 0;

  return (
    <main className="app-shell">
      <section className="broadcast-top" aria-label="PitchVolt broadcast header">
        <header className="broadcast-navigation">
          <div className="broadcast-brand">
            <img className="brand-logo" src="/pitchvolt-mark.svg" alt="" />
            <strong>
              PITCHVOLT <span>AI</span>
            </strong>
          </div>
          <nav className="broadcast-primary-nav" aria-label="Product navigation">
            <span className="current" aria-current="page">Live</span>
            <span>Matches</span>
            <span>Analysis</span>
            <span>Teams</span>
          </nav>
          <span className="broadcast-preview-label">SYNTHETIC REPLAY</span>
        </header>
        <div className="broadcast-scoreboard">
          <span className={`broadcast-live state-${streamState}`}>
            <span className="live-light" /> {streamState}
          </span>
          <div className="broadcast-score-content">
            <strong>Synthetic match</strong>
            <div className="broadcast-score-center">
              <span className="broadcast-score-unavailable" aria-label="Score unavailable">
                – : –
              </span>
              <span className="broadcast-match-clock">{clockLabel(matchClock)}</span>
            </div>
            <strong>Event replay</strong>
          </div>
        </div>
        <nav className="broadcast-tabs" aria-label="Match sections">
          <span className="selected" aria-current="page">Overview</span>
          <span>Tactical View</span>
          <span>Player Focus</span>
          <span>AI Commentary</span>
          <span>Key Moments</span>
        </nav>
      </section>

      <section className="control-bar" aria-label="Replay controls">
        <label>
          Scenario
          <select value={scenario} onChange={(event) => setScenario(event.target.value)}>
            {scenarios.map((item) => (
              <option key={item} value={item}>
                {item.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>

        <fieldset className="segmented">
          <legend className="visually-hidden">Replay speed</legend>
          {SPEEDS.map((item) => (
            <button
              className={speed === item ? "active" : ""}
              key={item}
              type="button"
              onClick={() => setSpeed(item)}
            >
              {item}×
            </button>
          ))}
        </fieldset>

        <button
          className="replay-button"
          type="button"
          onClick={() => setReplayNonce((n) => n + 1)}
        >
          Replay scenario
        </button>

        <fieldset className="segmented audience-switch">
          <legend className="visually-hidden">Audience mode</legend>
          {MODES.map((item) => (
            <button
              className={mode === item ? "active" : ""}
              key={item}
              type="button"
              onClick={() => setMode(item)}
            >
              {item}
            </button>
          ))}
        </fieldset>
      </section>

      {error ? <div className="error-banner">{error}</div> : null}
      {narrativeError ? <div className="error-banner">{narrativeError}</div> : null}

      <section className="broadcast-grid">
        <section className="panel insight-panel">
          <div className="panel-heading">
            <div>
              <h2>AI Insights</h2>
            </div>
            <span className="proof-badge">Evidence-backed</span>
          </div>

          {latestInsight ? (
            <InsightCard
              mode={mode}
              insight={latestInsight}
              narrative={narratives[latestInsight.insight_id] ?? null}
            />
          ) : (
            <div className="insight-placeholder" aria-live="polite">
              <strong>
                {selectedEvent
                  ? `Live action · ${eventLabel(selectedEvent)}`
                  : "Waiting for kickoff data…"}
              </strong>
              <span>
                {selectedEvent
                  ? `Observed ${selectedEvent.event_type.replaceAll("_", " ")} by ${displayName(selectedEvent.player_id)}. Tactical insight appears only after a verified sequence completes.`
                  : "The detector publishes tactical interpretation after a qualifying turnover-to-shot sequence."}
              </span>
            </div>
          )}
        </section>

        <Pitch event={selectedEvent} />
        <section className="panel key-moment-panel">
          <div className="panel-heading">
            <h2>Key Moment</h2>
          </div>
          <div className="key-moment-scene" aria-hidden="true">
            <span className="key-moment-ball" />
          </div>
          {selectedEvent ? (
            <div className="key-moment-copy">
              <strong>{clockLabel(selectedEvent.clock_ms)} · {eventLabel(selectedEvent)}</strong>
              <p>{displayName(selectedEvent.player_id)} · {displayName(selectedEvent.team_id)}</p>
              <span>Source-backed synthetic match event</span>
            </div>
           ) : (
            <p className="empty-state">Waiting for the next verified match event.</p>
          )}
          <button
            className="key-moment-button"
            type="button"
            onClick={() => {
              const message = messages.find((item) => isTacticalInsight(item));
              if (message) void inspect(message);
            }}
            disabled={!messages.some(isTacticalInsight)}
          >
            View Analysis →
          </button>
        </section>
        <div className="broadcast-detail-panels">
          <EventTimeline messages={messages} selectedId={selectedId} onSelect={inspect} />

          <section className="panel evidence-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">Evidence</span>
                <h2>Why this claim exists</h2>
              </div>
              <span className="count-badge">{evidence?.events.length ?? 0}</span>
            </div>

            {evidence ? (
              <div className="evidence-list">
                {evidence.events.map((event) => (
                  <button
                    key={event.event_id}
                    type="button"
                    onClick={() => {
                      const message = messages.find(
                        (candidate) =>
                          isMatchEvent(candidate) && candidate.payload.event_id === event.event_id,
                      );
                      if (message) setSelectedId(message.id);
                    }}
                  >
                    <span>{clockLabel(event.clock_ms)}</span>
                    <strong>{event.event_type}</strong>
                    <small>{displayName(event.player_id)}</small>
                  </button>
                ))}
                <p className="evidence-footnote">
                  Source IDs and metrics are returned by the deterministic evidence endpoint.
                </p>
              </div>
            ) : (
              <p className="empty-state">
                Select a tactical insight in the timeline to inspect its contributing events.
              </p>
            )}
          </section>
        </div>
      </section>

      <footer>
        <span>Ingest → Interpret → Explain → Render → Personalize</span>
        <span>Local controlled narratives · Foundry inference disabled</span>
      </footer>
    </main>
  );
}

function InsightCard({
  mode,
  insight,
  narrative,
}: {
  mode: AudienceMode;
  insight: TacticalInsight;
  narrative: NarrativeUpdate | null;
}) {
  const duration = insight.metrics.transition_duration_ms;
  const actions = insight.metrics.attacking_actions;

  return (
    <article className="insight-card">
      <div className="insight-title">
        <span>{insight.kind.replaceAll("_", " ")}</span>
        <strong>{displayName(insight.team_id)}</strong>
      </div>

      <p className="mode-copy">{modeCopy(mode, insight)}</p>

      <div className="metric-grid">
        <div>
          <span>Transition</span>
          <strong>{typeof duration === "number" ? `${(duration / 1000).toFixed(1)}s` : "—"}</strong>
        </div>
        <div>
          <span>Actions</span>
          <strong>{typeof actions === "number" ? actions : "—"}</strong>
        </div>
        <div>
          <span>Evidence</span>
          <strong>{insight.evidence_event_ids.length}</strong>
        </div>
      </div>

      <div className="narrative-status">
        {narrative ? (
          <>
            <strong>{narrative.headline}</strong>
            <p>{narrative.text}</p>
            <small>Local controlled narrative · No model inference</small>
          </>
        ) : (
          "Deterministic audience preview · local narrative pending · Foundry disabled"
        )}
      </div>
    </article>
  );
}
