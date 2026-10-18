# Offline StatsBomb 360 source-frame viewer

Use this inspection tool only with locally stored **original** files whose
SHA-256 fingerprints have been verified. It is not the fictional live replay
and does not publish source data to Azure, a CDN, a web endpoint or an LLM.

1. Acquire the same-commit event, lineup and 360 files explicitly:
   `uv run --frozen python -m pitchvolt.statsbomb_bundle_acquire --commit 4b73468fc5b0f1950f9f66fada70ad3a4f9327cb --match-id 3764440 --output-dir .local-statsbomb/3764440 --include-360 --execute-download`.
2. Pick an **original event UUID** from the acquired 360 JSON whose snapshot
   you want to inspect. Do not substitute a fictional replay event ID.
3. Run `uv run --frozen python -m pitchvolt.statsbomb_360_preview --directory .local-statsbomb/3764440 --match-id 3764440 --event-id <SOURCE_UUID> --lineup-sha256 7d3365b7ced12e3e2de50f6ecd076d088e94bbc769492ae4aa5867898f592fc0 --frame-sha256 1f33de0d962233529356e1bd8970d0015f4ad0c165065fcdf521c714f06ecee5 --output .local-statsbomb/frame.html`.
4. Open the locally generated HTML in a browser; outputs refuse overwrite.

The zero-dependency SVG visualizes **only** canonical in-field coordinates
from the requested source frame. Off-field source observations are retained
for the verified coverage count but not clamped onto the drawing.
Blue/amber distinguish source-relative teammates and opponents, not
assumed home/away identities; only the source actor is identifiable.
No result claims continuous tracking or inferred movement. 22 detections
are shown only in a genuinely complete 360 frame.

This is a research/validation utility, not a substitute for PitchVolt's
WebGL live experience. A hosted historical mode requires explicit
redistribution/attribution review and source-backed transport. Source:
StatsBomb Open Data by Hudl, https://github.com/hudl/open-data .

## Genuine full-XI source gallery (offline only)

To inspect every original 360 event in this pinned source match with **11
teammates and 11 opponents simultaneously observed**, keep the same three
verified inputs and replace `--event-id` with `--full-xi-gallery`:

```sh
uv run --frozen python -m pitchvolt.statsbomb_360_preview \
  --directory .local-statsbomb/3764440 --match-id 3764440 \
  --full-xi-gallery \
  --lineup-sha256 7d3365b7ced12e3e2de50f6ecd076d088e94bbc769492ae4aa5867898f592fc0 \
  --frame-sha256 1f33de0d962233529356e1bd8970d0015f4ad0c165065fcdf521c714f06ecee5 \
  --output .local-statsbomb/full-xi-frames.html
```

Open the generated HTML locally. Its collapsible event panels reuse the
single-frame source renderer, each labelled with the **original event UUID**
and source clock, and display no positions beyond that exact verified event.
All other players remain anonymous except the source-identified event actor.
No images or original JSON are uploaded or hosted.

A prior source audit recorded **8 complete observed 11v11 frames among 3,914
available freeze frames for match 3764440**. This is a highly sparse
coverage subset, **not an 11v11 continuous replay**. Some originally observed
players may be off-field and are counted but not rendered on the pitch.
For a different match, the gallery may contain zero complete frames.
