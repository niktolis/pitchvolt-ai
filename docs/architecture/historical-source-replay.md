# IDSSE source-observed historical 3D replay — Issue #153

The approved tracking data source is the **Deutsche Fußball Liga (DFL)
IDSSE/Sportec Open Dataset**, CC BY 4.0 (separate from the AGPLv3
repository code license). Original research publication: Bassek et al.
(2025), *Scientific Data*, DOI
https://doi.org/10.1038/s41597-025-04505-y.

**Recorded fixture**: 1. FC Köln vs FC Bayern München, 27 May 2023,
source match `DFL-MAT-J03WMX`, first-half source frames
**12219–12843**, 625 samples at 25 Hz. Source shot event
`18226500000041` is at frame **12519**.

## Independently source-verified input

- Entire original immutable tracking XML pinned to
  SHA-256 `d3dd92e509421a6466acb0a083c009035f1751bc5fd9ef42ffa8f20d01cf7d49`.
- Deterministic 381,441-byte derived clip SHA-256
  `d1b6dda14d84a266cd26ef607c12b62712fe906a8de9c9b75be860b464346db6`.
- Source verification and deterministic exporter: PR #152,
  [Actions run 39258654058](https://github.com/niktolis/pitchvolt-ai/actions/runs/39258654058).
- The **pinned derived** JSON was promoted once by a branch-limited,
  repository-owned workflow that checked its exact digest and decoded
  every frame before committing `web/public/historical/j03wmx-shot-12519-observed-v1.json`
  to the review branch. Once merged it is a durable same-origin web asset
  bundled into the existing production image, **not** a temporary
  Actions artifact dependency and not the original 419 MB XML.
- See [full source audit](idsse-sportec-acquisition.md).

## Client boundary and precise rendering semantics

`web/src/domain/historicalReplay.ts` verifies the exact source
artifact SHA-256 via browser Web Crypto before parsing the v1
observation contract, match identity, CC BY attribution, 22 unique
source players (11+11), 625 exact frame IDs at 25 Hz, and measured
ball XYZ (no synthesized ball carrier).

`web/src/components/HistoricalTrackingScene.tsx` reuses the existing
3D Turf, FieldMarkings, GoalFrame, and neutral geometric
`FootballActorAvatar`. Every athlete is rendered at the current
**measured source XY**. The ball uses current **measured XYZ** including
real elevation. Uniform colors and generic human geometry are
**illustrative art only**, not player-recognition, athletic pose or
club-logo evidence. Neutral `K` and `B` team badges do not reproduce
licensed football club crests.

The source coordinate transform is:
`world_x = canonical_pitch_x - 52.5`,
`world_z = canonical_pitch_y - 34`,
`world_y = measured_ball_z`.
No player or ball movement is interpolated between samples, and the
browser never invents formation or substitutes missing source points.

`HistoricalReplay.tsx` is a **distinct mode** in the same approved
three-column broadcast frame. It includes its own source-qualified
header, observations panel, on-pitch Three.js player and ball movement,
independent Key Moment 3D source-shot view, and under-pitch 25 Hz
play/pause/±2s/seek/speed controls. The shot shortcut seeks exactly to
frame 12519. Existing synthetic SSE, evidence, Foundry controls and
narratives remain unchanged in the alternative `SyntheticApp` mode.

No model-generated analyst/storyteller statement is attached to the
historical fixture because the source only verifies a shot event and
measured positions, not an individual ball carrier, pressure
determination, match score at the excerpt, or shot outcome. The
in-app historical attribution credits DFL, CC BY 4.0, and the paper.

## Acceptance gates

- CI frontend lint/typecheck/unit tests/build; Python plus architecture
  checks; reviewed asset is included in Docker web build.
- Dedicated browser tests reject changed frame IDs, unknown/source-missing
  player positions, wrong event/match, timestamp gaps, changed ball
  height and missing/published-unverified assets.
- **Visual acceptance still requires a deployed screenshot** compared
  to the authoritative branded 1672 × 941 reference. Do not infer
  visual perfection from green unit tests. The user will upload the
  deployed actual screenshot.
- Manager approval required before merge. Do not initiate extra
  Foundry inference, provision Azure resources or bypass main rules.
