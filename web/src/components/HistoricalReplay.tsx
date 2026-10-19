import { useCallback, useEffect, useMemo, useState } from "react";
import {
  exactFrameAtCursor,
  HISTORICAL_FIRST_FRAME,
  HISTORICAL_FRAME_COUNT,
  HISTORICAL_LAST_CURSOR_MS,
  HISTORICAL_SHOT_FRAME,
  loadHistoricalClip,
  type HistoricalClip,
} from "../domain/historicalReplay";
import { HistoricalTrackingScene } from "./HistoricalTrackingScene";

const PLAYBACK_SPEEDS = [1, 2, 4] as const;
const SHOT_OFFSET_MS = (HISTORICAL_SHOT_FRAME - HISTORICAL_FIRST_FRAME) * 40;

const timeLabel = (ms: number) => {
  const secs = Math.floor(ms / 1000);
  return `${String(Math.floor(secs / 60)).padStart(2, "0")}:${String(secs % 60).padStart(2, "0")}`;
};

export function HistoricalReplay({ onSynthetic }: { onSynthetic: () => void }) {
  const [clip, setClip] = useState<HistoricalClip | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState<number>(1);

  useEffect(() => {
    let active = true;
    void loadHistoricalClip()
      .then((source) => {
        if (active) setClip(source);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "Historical source unavailable");
          setPlaying(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!clip || !playing) return;
    let last = performance.now();
    let elapsedFraction = 0;
    const timer = window.setInterval(() => {
      const now = performance.now();
      elapsedFraction += (now - last) * speed;
      last = now;
      const sampleSteps = Math.floor(elapsedFraction / 40);
      if (sampleSteps === 0) return;
      elapsedFraction -= sampleSteps * 40;
      setFrameIndex((current) => Math.min(HISTORICAL_FRAME_COUNT - 1, current + sampleSteps));
    }, 40);
    return () => window.clearInterval(timer);
  }, [playing, speed, clip]);

  useEffect(() => {
    if (frameIndex >= HISTORICAL_FRAME_COUNT - 1) setPlaying(false);
  }, [frameIndex]);

  const elapsedMs = frameIndex * 40;
  const frame = useMemo(
    () => (clip ? exactFrameAtCursor(clip, elapsedMs) : null),
    [clip, elapsedMs],
  );
  const shot = useMemo(
    () => (clip ? exactFrameAtCursor(clip, SHOT_OFFSET_MS) : null),
    [clip],
  );
  const home = clip?.match.teams.find((team) => team.role === "home");
  const away = clip?.match.teams.find((team) => team.role === "away");
  const shotReached = frameIndex >= HISTORICAL_SHOT_FRAME - HISTORICAL_FIRST_FRAME;

  const seekTo = useCallback((nextIndex: number) => {
    setFrameIndex(Math.max(0, Math.min(HISTORICAL_FRAME_COUNT - 1, nextIndex)));
    setPlaying(false);
  }, []);

  return (
    <main className="app-shell historical-app">
      <section className="broadcast-top" aria-label="PitchVolt historical replay header">
        <header className="broadcast-navigation">
          <div className="broadcast-brand">
            <img className="brand-logo" src="/pitchvolt-mark.svg" alt="" />
            <strong>PITCHVOLT <span>AI</span></strong>
          </div>
          <nav className="broadcast-primary-nav" aria-label="Replay mode navigation">
            <span className="current" aria-current="page">Historical replay</span>
            <button type="button" className="historical-nav-button" onClick={onSynthetic}>
              Synthetic / AI demo
            </button>
          </nav>
          <div className="broadcast-utilities">
            <span className="broadcast-preview-label">RECORDED DATA · IDSSE / DFL</span>
            <span className="historical-source-indicator">SOURCE-VERIFIED 25 Hz</span>
          </div>
        </header>
        <div className="broadcast-scoreboard">
          <span className="broadcast-live state-live">
            <span className="live-light" /> RECORDED · 2023
          </span>
          <div className="broadcast-score-content">
            <div className="broadcast-fixture-team broadcast-fixture-home">
              <strong>{home?.name ?? "1. FC Köln"}</strong>
              <span className="broadcast-team-shield shield-home" aria-label="Neutral home team emblem">K</span>
            </div>
            <div className="broadcast-score-center">
              <span className="broadcast-score-unavailable" title="Score is not established by this 25-second source clip">
                – : –
              </span>
              <span className="broadcast-match-clock">{timeLabel(elapsedMs)}</span>
            </div>
            <div className="broadcast-fixture-team broadcast-fixture-away">
              <span className="broadcast-team-shield shield-away" aria-label="Neutral away team emblem">B</span>
              <strong>{away?.name ?? "FC Bayern München"}</strong>
            </div>
          </div>
        </div>
        <nav className="broadcast-tabs" aria-label="Historical match sections">
          <span className="selected" aria-current="page">Observed tracking</span>
          <span>22 recorded players</span>
          <span>Ball XYZ</span>
          <span>Source event replay</span>
        </nav>
      </section>

      {error ? (
        <div className="error-banner" role="alert">
          Verified IDSSE replay unavailable: {error}. No illustrative movement will be substituted.
          <button type="button" className="replay-button" onClick={onSynthetic}>
            Open synthetic demo
          </button>
        </div>
      ) : null}

      <section className="broadcast-grid historical-grid">
        <section className="panel insight-panel" aria-label="Historical source evidence">
          <div className="panel-heading">
            <div><h2>Source Insights</h2></div>
            <span className="proof-badge">Measured</span>
          </div>
          <div className="historical-source-facts">
            <strong>Authentic Bundesliga match</strong>
            <p>Recorded event and tracking observations—not generative predictions.</p>
            <div className="historical-metric-pair">
              <span>Observed players</span>
              <strong>{frame ? frame.players_xy_m.filter((p) => p !== null).length : "—"} / 22</strong>
            </div>
            <div className="historical-metric-pair">
              <span>Tracked ball elevation</span>
              <strong>{frame ? `${frame.ball_xyz_m[2].toFixed(2)} m` : "—"}</strong>
            </div>
            <div className="historical-metric-pair">
              <span>Source frame</span>
              <strong>{frame?.source_frame ?? "—"}</strong>
            </div>
            <div className="historical-metric-pair">
              <span>Source sample rate</span>
              <strong>25 Hz</strong>
            </div>
            <p className="historical-provenance">
              Team possession markers are not proof of an individual ball carrier.
              No player paths, formations, duels, or ball locations are inferred.
            </p>
            <button type="button" className="historical-shot-action" disabled={!clip}
              onClick={() => seekTo(HISTORICAL_SHOT_FRAME - HISTORICAL_FIRST_FRAME)}>
              Jump to recorded shot ↗
            </button>
          </div>
        </section>

        <section className="panel pitch-panel historical-pitch-panel" aria-label="3D recorded match tracking">
          {clip && frame ? (
            <div className="pitch">
              <HistoricalTrackingScene clip={clip} frame={frame} />
            </div>
          ) : (
            <div className="historical-pitch-loading">
              {error ? "Source replay could not be verified." : "Verifying original match asset and player/ball observations…"}
            </div>
          )}
          <div className="pitch-ball-status">
            <strong>Observed 22-player tracking · 25 source frames per second</strong>
            <small>Exact frames only · DFL IDSSE · Camera is illustrative; player and ball locations are measured</small>
          </div>
        </section>

        <section className="panel key-moment-panel" aria-label="Source-linked key moment">
          <div className="panel-heading">
            <h2>Key Moment</h2>
            <span className="proof-badge">Source event</span>
          </div>
          {clip && shot ? (
            <div className="historical-shot-view">
              <HistoricalTrackingScene clip={clip} frame={shot} shotFocus />
            </div>
          ) : (
            <div className="historical-shot-placeholder">
              {error ? "Source cannot be verified" : "Loading measured shot position…"}
            </div>
          )}
          <div className="historical-source-facts">
            <strong>Recorded shot at goal</strong>
            <p>
              {shotReached ? "Reached in replay" : "Upcoming in replay"}
              {" · "}Source event 18226500000041
            </p>
            <div className="historical-metric-pair">
              <span>Exact event frame</span>
              <strong>{HISTORICAL_SHOT_FRAME}</strong>
            </div>
            <div className="historical-metric-pair">
              <span>Ball height at shot</span>
              <strong>{shot ? `${shot.ball_xyz_m[2].toFixed(2)} m` : "—"}</strong>
            </div>
            <small>Player carrier and shot outcome are not established by this clip.</small>
          </div>
        </section>

        <section className="pitch-replay-deck historical-replay-controls" aria-label="Historical replay controls">
          <div className="historical-source-clock">
            <span>{timeLabel(elapsedMs)}</span>
            <span>Original frame {frame?.source_frame ?? "—"} · 25 s clip</span>
          </div>
          <input
            type="range" aria-label="Seek to exact source tracking frame"
            min={0} max={HISTORICAL_FRAME_COUNT - 1} step={1} value={frameIndex}
            disabled={!clip}
            onChange={(event) => seekTo(Number(event.target.value))}
          />
          <div className="historical-playback-actions">
            <button className="replay-button" type="button" disabled={!clip}
              onClick={() => {
                if (frameIndex === HISTORICAL_FRAME_COUNT - 1) setFrameIndex(0);
                setPlaying((wasPlaying) => !wasPlaying || frameIndex === HISTORICAL_FRAME_COUNT - 1);
              }}>
              {playing && frameIndex < HISTORICAL_FRAME_COUNT - 1 ? "Pause" : "Play"}
            </button>
            <button className="replay-button" type="button" disabled={!clip}
              onClick={() => seekTo(frameIndex - 50)} aria-label="Back two source-observed seconds">
              −2s
            </button>
            <button className="replay-button" type="button" disabled={!clip}
              onClick={() => seekTo(frameIndex + 50)} aria-label="Forward two source-observed seconds">
              +2s
            </button>
            <fieldset className="segmented">
              <legend className="visually-hidden">Playback speed</legend>
              {PLAYBACK_SPEEDS.map((value) => (
                <button key={value} className={speed === value ? "active" : ""}
                  type="button" onClick={() => setSpeed(value)}>{value}×</button>
              ))}
            </fieldset>
            <button type="button" className="replay-button" onClick={() => seekTo(0)} disabled={!clip}>
              Restart
            </button>
          </div>
        </section>
      </section>

      <footer className="historical-attribution">
        <span>
          {clip?.source.attribution ??
            "Deutsche Fußball Liga · IDSSE/Sportec Open Data · CC BY 4.0 · Bassek et al. (2025)"}
        </span>
        <span>Historical source replay · No Foundry inference</span>
      </footer>
      <span className="visually-hidden" aria-live="polite">
        {frame
          ? `Showing source frame ${frame.source_frame} of ${HISTORICAL_FIRST_FRAME + HISTORICAL_FRAME_COUNT - 1}.`
          : "Historical replay awaiting authentication."}
      </span>
    </main>
  );
}
