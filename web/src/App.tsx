import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  fetchEvidence,
  fetchPresentation,
  fetchScenarios,
  fetchTimeline,
  openNarrativeStream,
} from "./api/client";
import type {
  EvidenceResponse,
  MatchEvent,
  MatchPresentation,
  NarrativeUpdate,
  ReplayMessage,
  TacticalInsight,
} from "./api/types";
import { isMatchEvent, isTacticalInsight } from "./api/types";
import { EventTimeline } from "./components/EventTimeline";
import { Pitch } from "./components/Pitch";
import { SourceMomentPreview } from "./components/SourceMomentPreview";
import {
  lineupAtCursor,
  playerLabel,
  scoreAtCursor,
  teamLabel,
} from "./domain/fixturePresentation";
import {
  type AudienceMode,
  clockLabel,
  displayName,
  eventLabel,
  modeCopy,
} from "./domain/presentation";
import {
  clampCursor,
  isEvidenceVisible,
  latestAtCursor,
  matchBounds,
  narrativeStateKey,
  publishedNarrativeAtCursor,
  recentInsightsAtCursor,
  selectedAtCursor,
} from "./domain/replayClock";

const SPEEDS = [1, 5, 25] as const;
const MODES: AudienceMode[] = ["casual", "analyst", "club"];

export function App() {
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [scenario, setScenario] = useState("");
  const [speed, setSpeed] = useState<number>(5);
  const [mode, setMode] = useState<AudienceMode>("casual");
  const [messages, setMessages] = useState<ReplayMessage[]>([]);
  const [presentation, setPresentation] = useState<MatchPresentation | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [narratives, setNarratives] = useState<Record<string, NarrativeUpdate>>({});
  const [narrativeError, setNarrativeError] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<EvidenceResponse | null>(null);
  const [streamState, setStreamState] = useState<"connecting" | "live" | "complete" | "error">(
    "connecting",
  );
  const [error, setError] = useState<string | null>(null);
  const [replayNonce, setReplayNonce] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [cursorMs, setCursorMs] = useState(0);
  const evidenceRequestEpoch = useRef(0);
  const currentCursorMs = useRef(0);

  useEffect(() => {
    currentCursorMs.current = cursorMs;
  }, [cursorMs]);

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

  // biome-ignore lint/correctness/useExhaustiveDependencies: replayNonce restarts the snapshot.
  useEffect(() => {
    if (!scenario) return;
    let active = true;
    evidenceRequestEpoch.current += 1;
    setMessages([]);
    setPresentation(null);
    setSelectedId(null);
    setEvidence(null);
    setError(null);
    setPlaying(true);
    setCursorMs(0);
    setStreamState("connecting");
    void Promise.all([fetchTimeline(scenario), fetchPresentation(scenario)])
      .then(([loaded, authored]) => {
        if (loaded.length && loaded[0]?.match_id !== authored.match_id) {
          throw new Error("Mismatched replay and presentation fixture identity");
        }
        if (!active) return;
        setMessages(loaded);
        setPresentation(authored);
        setCursorMs(matchBounds(loaded).start);
        setStreamState(loaded.length ? "live" : "complete");
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setError(reason instanceof Error ? reason.message : "Unable to load timeline.");
        setStreamState("error");
      });
    return () => {
      active = false;
    };
  }, [scenario, replayNonce]);

  const bounds = useMemo(() => matchBounds(messages), [messages]);
  const homeName = presentation?.home.name ?? "Synthetic match";
  const awayName = presentation?.away.name ?? "Event replay";
  const replayScore = scoreAtCursor(presentation, cursorMs);
  const replayLineup = lineupAtCursor(presentation, cursorMs);

  useEffect(() => {
    if (!playing || messages.length === 0) return;
    let previous = performance.now();
    const timer = window.setInterval(() => {
      const now = performance.now();
      const elapsed = Math.max(0, now - previous);
      previous = now;
      setCursorMs((current) => Math.min(bounds.end, current + elapsed * speed));
    }, 50);
    return () => window.clearInterval(timer);
  }, [playing, speed, messages.length, bounds.end]);

  useEffect(() => {
    if (messages.length > 0 && cursorMs >= bounds.end) {
      setPlaying(false);
      setStreamState("complete");
    }
  }, [cursorMs, bounds.end, messages.length]);

    useEffect(() => {
    if (!scenario) return undefined;
    setNarratives({});
    setNarrativeError(null);
    let active = true;
    const close = openNarrativeStream(scenario, mode, {
      onNarrative: (message) => {
        if (active) {
          setNarratives((current) => ({
            ...current,
            [narrativeStateKey(scenario, mode, replayNonce, message.insight_id)]: message,
          }));
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

  const replay = useMemo(() => latestAtCursor(messages, cursorMs), [messages, cursorMs]);
  const visibleMessages = replay.visible;
  const selected = selectedAtCursor(visibleMessages, selectedId, cursorMs, playing);
  const latestInsight = replay.insight;
  const recentInsights = useMemo(
    () => recentInsightsAtCursor(messages, cursorMs),
    [messages, cursorMs],
  );
  const displayEvidence =
    evidence && isEvidenceVisible(messages, cursorMs, evidence.insight_id) ? evidence : null;
  const selectedEvent: MatchEvent | null =
    selected && isMatchEvent(selected) ? selected.payload : replay.event;

  const inspect = useCallback(
    async (message: ReplayMessage) => {
      const requestEpoch = ++evidenceRequestEpoch.current;
      currentCursorMs.current = message.payload.clock_ms;
      setCursorMs(message.payload.clock_ms);
      setEvidence(null);
      setSelectedId(message.id);
      setPlaying(false);
      if (!isTacticalInsight(message) || !scenario) {
        setEvidence(null);
        return;
      }
      try {
        const result = await fetchEvidence(scenario, message.payload.insight_id);
        if (
          requestEpoch === evidenceRequestEpoch.current &&
          currentCursorMs.current >= message.payload.clock_ms &&
          result.insight_id === message.payload.insight_id
        ) {
          setEvidence(result);
        }
      } catch (reason: unknown) {
        if (requestEpoch === evidenceRequestEpoch.current) {
          setError(reason instanceof Error ? reason.message : "Unable to load evidence.");
        }
      }
    },
    [scenario],
  );

  const togglePlayback = useCallback(() => {
    if (playing) {
      setPlaying(false);
      return;
    }
    if (cursorMs >= bounds.end) {
      setCursorMs(bounds.start);
      setSelectedId(null);
      setEvidence(null);
    }
    setSelectedId(null);
    setPlaying(true);
    setStreamState("live");
  }, [playing, cursorMs, bounds.start, bounds.end]);

  const matchClock = cursorMs;

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
            <span className="current" aria-current="page">
              Live
            </span>
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
            <div className="broadcast-fixture-team broadcast-fixture-home">
              <strong>{homeName}</strong>
              <span
                className="broadcast-team-shield shield-home"
                aria-hidden="true"
                style={
                  presentation
                    ? {
                        background: `linear-gradient(155deg, ${presentation.home.primary_color}, ${presentation.home.secondary_color})`,
                      }
                    : undefined
                }
              >
                {presentation?.home.emblem_text ?? homeName.slice(0, 1)}
              </span>
            </div>
            <div className="broadcast-score-center">
              <span
                className={replayScore ? "broadcast-score-known" : "broadcast-score-unavailable"}
                title={
                  replayScore
                    ? "Score from explicit canonical goal events"
                    : "Score not established by this excerpt"
                }
              >
                {replayScore ? `${replayScore.home} : ${replayScore.away}` : "– : –"}
              </span>
              <span className="broadcast-match-clock">{clockLabel(matchClock)}</span>
            </div>
            <div className="broadcast-fixture-team broadcast-fixture-away">
              <span
                className="broadcast-team-shield shield-away"
                aria-hidden="true"
                style={
                  presentation
                    ? {
                        background: `linear-gradient(155deg, ${presentation.away.primary_color}, ${presentation.away.secondary_color})`,
                      }
                    : undefined
                }
              >
                {presentation?.away.emblem_text ?? awayName.slice(0, 1)}
              </span>
              <strong>{awayName}</strong>
            </div>
          </div>
        </div>
        <details className="broadcast-roster">
          <summary>
            Team rosters &amp; substitutions <span>Source-authored fiction</span>
          </summary>
          {presentation ? (
            <div className="broadcast-roster-grid">
              {[presentation.home, presentation.away].map((team) => {
                const active =
                  team.team_id === presentation.home.team_id
                    ? replayLineup?.home_active
                    : replayLineup?.away_active;
                const playerById = new Map(
                  team.players.map((player) => [player.player_id, player]),
                );
                const visibleChanges = presentation.substitutions.filter(
                  (change) => change.team_id === team.team_id && change.clock_ms <= cursorMs,
                );
                return (
                  <section key={team.team_id} aria-label={`${team.name} roster`}>
                    <h3>
                      {team.name} <small>Coach: {team.coach}</small>
                    </h3>
                    {active ? (
                      <ol className="roster-active-list">
                        {active.map((id) => (
                          <li key={id}>
                            <span>{playerById.get(id)?.jersey_number ?? "–"}</span>{" "}
                            {playerById.get(id)?.surname ?? "Unknown"}
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p>Starting XI not established for this excerpt.</p>
                    )}
                    <div className="roster-substitutions" aria-live="polite">
                      {visibleChanges.map((change) => (
                        <p key={change.event_id}>
                          <strong>{clockLabel(change.clock_ms)}</strong>
                          <span className="roster-out">
                            ↓ {playerById.get(change.outgoing_player_id)?.surname ?? "Unknown"}
                          </span>
                          <span className="roster-in">
                            ↑ {playerById.get(change.incoming_player_id)?.surname ?? "Unknown"}
                          </span>
                        </p>
                      ))}
                    </div>
                  </section>
                );
              })}
            </div>
          ) : (
            <p>Loading verified fixture metadata…</p>
          )}
        </details>
        <nav className="broadcast-tabs" aria-label="Match sections">
          <span className="selected" aria-current="page">
            Overview
          </span>
          <span>Tactical View</span>
          <span>Player Focus</span>
          <span>AI Commentary</span>
          <span>Key Moments</span>
        </nav>
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

          {recentInsights.length > 0 ? (
            <>
              <div className="verified-insight-feed">
                {recentInsights.map((message) => (
                  <button
                    className="verified-insight-row"
                    key={message.payload.insight_id}
                    type="button"
                    onClick={() => void inspect(message)}
                  >
                    <span className="verified-insight-icon" aria-hidden="true">
                      ◈
                    </span>
                    <span className="verified-insight-copy">
                      <strong>
                        {message.payload.kind.replaceAll("_", " ")} ·{" "}
                        {displayName(message.payload.team_id)}
                      </strong>
                      <span>{modeCopy(mode, message.payload)}</span>
                      <small>
                        {clockLabel(message.payload.clock_ms)} ·{" "}
                        {message.payload.evidence_event_ids.length} source events
                      </small>
                    </span>
                  </button>
                ))}
              </div>
              {latestInsight ? (
                <details className="insight-metrics-details">
                  <summary>Detailed verified metrics</summary>
                  <InsightCard
                    mode={mode}
                    insight={latestInsight}
                    narrative={publishedNarrativeAtCursor(
                      messages,
                      cursorMs,
                      scenario,
                      mode,
                      replayNonce,
                      latestInsight.insight_id,
                      narratives,
                    )}
                  />
                </details>
              ) : null}
            </>
          ) : (
            <div className="insight-placeholder" aria-live="polite">
              <strong>
                {selectedEvent
                  ? `Live action · ${eventLabel(selectedEvent)}`
                  : "Waiting for kickoff data…"}
              </strong>
              <span>
                {selectedEvent
                  ? `Observed ${selectedEvent.event_type.replaceAll("_", " ")} by ${playerLabel(presentation, selectedEvent.player_id)}. Tactical insight appears only after a verified sequence completes.`
                  : "The detector publishes tactical interpretation after a qualifying turnover-to-shot sequence."}
              </span>
            </div>
          )}
        </section>

        <Pitch
          event={selectedEvent}
          actorLabel={
            selectedEvent ? playerLabel(presentation, selectedEvent.player_id) : undefined
          }
          actorColor={
            presentation && selectedEvent?.team_id === presentation.away.team_id
              ? presentation.away.primary_color
              : presentation?.home.primary_color
          }
          playing={playing}
          canReplay={messages.length > 0}
          onTogglePlayback={togglePlayback}
        >
          <EventTimeline
            messages={visibleMessages}
            selectedId={selectedId}
            cursorMs={cursorMs}
            onSelect={inspect}
          />
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

            <fieldset className="replay-seek-controls">
              <legend className="visually-hidden">Timeline playback controls</legend>
              <button type="button" onClick={togglePlayback} disabled={!messages.length}>
                {playing ? "Pause" : "Play"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setCursorMs((c) => clampCursor(c - 2000, bounds.start, bounds.end));
                  setPlaying(false);
                  setSelectedId(null);
                }}
                disabled={!messages.length}
                aria-label="Back 2 seconds"
              >
                −2s
              </button>
              <label>
                Match clock
                <input
                  type="range"
                  min={bounds.start}
                  max={Math.max(bounds.start + 1, bounds.end)}
                  step={100}
                  value={cursorMs}
                  onChange={(event) => {
                    setCursorMs(Number(event.target.value));
                    setPlaying(false);
                    setSelectedId(null);
                  }}
                  disabled={!messages.length}
                  aria-label="Seek match time"
                  aria-valuetext={clockLabel(cursorMs)}
                />
              </label>
              <button
                type="button"
                onClick={() => {
                  setCursorMs((c) => clampCursor(c + 2000, bounds.start, bounds.end));
                  setPlaying(false);
                  setSelectedId(null);
                }}
                disabled={!messages.length}
                aria-label="Forward 2 seconds"
              >
                +2s
              </button>
            </fieldset>

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
        </Pitch>
        <section className="panel key-moment-panel">
          <div className="panel-heading">
            <h2>Key Moment</h2>
          </div>
          <SourceMomentPreview event={selectedEvent} />
          {selectedEvent ? (
            <div className="key-moment-copy">
              <strong>{eventLabel(selectedEvent)}</strong>
              <p>
                {playerLabel(presentation, selectedEvent.player_id)} ·{" "}
                {teamLabel(presentation, selectedEvent.team_id)}
              </p>
              <span>Source-backed synthetic match event</span>
            </div>
          ) : (
            <p className="empty-state">Waiting for the next verified match event.</p>
          )}
          <button
            className="key-moment-button"
            type="button"
            onClick={() => {
              const message = recentInsights[0];
              if (message) void inspect(message);
            }}
            disabled={!visibleMessages.some(isTacticalInsight)}
          >
            View Analysis →
          </button>
        </section>
        <div className="broadcast-detail-panels">
          <section className="panel evidence-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">Evidence</span>
                <h2>Why this claim exists</h2>
              </div>
              <span className="count-badge">{displayEvidence?.events.length ?? 0}</span>
            </div>

            {displayEvidence ? (
              <div className="evidence-list">
                {displayEvidence.events.map((event) => (
                  <button
                    key={event.event_id}
                    type="button"
                    onClick={() => {
                      const message = visibleMessages.find(
                        (candidate) =>
                          isMatchEvent(candidate) && candidate.payload.event_id === event.event_id,
                      );
                      if (message) void inspect(message);
                    }}
                  >
                    <span>{clockLabel(event.clock_ms)}</span>
                    <strong>{event.event_type}</strong>
                    <small>{playerLabel(presentation, event.player_id)}</small>
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
  const possession = insight.kind === "sustained_possession";
  const duration = insight.metrics[possession ? "sequence_duration_ms" : "transition_duration_ms"];
  const actions = insight.metrics[possession ? "passes" : "attacking_actions"];

  return (
    <article className="insight-card">
      <div className="insight-title">
        <span>{insight.kind.replaceAll("_", " ")}</span>
        <strong>{displayName(insight.team_id)}</strong>
      </div>

      <p className="mode-copy">{modeCopy(mode, insight)}</p>

      <div className="metric-grid">
        <div>
          <span>{possession ? "Possession" : "Transition"}</span>
          <strong>{typeof duration === "number" ? `${(duration / 1000).toFixed(1)}s` : "—"}</strong>
        </div>
        <div>
          <span>{possession ? "Passes" : "Actions"}</span>
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
