import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Pitch } from "./Pitch";

describe("source-backed tactical pitch control placement", () => {
  it("shows exactly one seek slider immediately beneath the pitch, ahead of ball facts and event feed", () => {
    const html = renderToStaticMarkup(
      <Pitch
        event={null}
        cursorMs={120_000}
        playing={false}
        canReplay={true}
        onTogglePlayback={() => {}}
        seekControls={
          <fieldset className="replay-seek-controls">
            <legend>Match time controls</legend>
            <input type="range" aria-label="Seek match time" min={0} max={300_000} value={120_000} readOnly />
          </fieldset>
        }
      >
        <section aria-label="Recorded match events">Event feed</section>
      </Pitch>,
    );

    const pitch = html.indexOf('class="pitch"');
    const seek = html.indexOf('class="pitch-seek-strip"');
    const ball = html.indexOf('class="pitch-ball-status"');
    const events = html.indexOf('class="pitch-replay-deck"');

    expect(pitch).toBeGreaterThanOrEqual(0);
    expect(seek).toBeGreaterThan(pitch);
    expect(ball).toBeGreaterThan(seek);
    expect(events).toBeGreaterThan(ball);
    expect(html.match(/aria-label="Seek match time"/g)).toHaveLength(1);
    expect(html.match(/type="range"/g)).toHaveLength(1);
  });

  it("does not render an inert empty scrubber when controls are unavailable", () => {
    const html = renderToStaticMarkup(
      <Pitch
        event={null}
        cursorMs={0}
        playing={false}
        canReplay={false}
        onTogglePlayback={() => {}}
      />,
    );
    expect(html).not.toContain('class="pitch-seek-strip"');
  });
});
