# Broadcast pitch rendering stack

The approved PitchVolt AI Application Preview is the sole visual specification.
The implementation is not accepted until a browser capture of the deployed
application has been reviewed against that exact image.

## Rendering tools (locked dependencies)

- **three 0.186.1**: WebGL geometry, materials, shadows, field lighting,
  and camera projection.
- **@react-three/fiber 9.8.1**: React 19-compatible declarative scene lifecycle.
- **@react-three/drei 10.7.9**: production-ready camera, model, and scene helpers.
- **@types/three 0.186.0**: compile-time types for geometry and scene APIs.
- **Existing React + CSS**: stadium background, scoreboard, responsive three-card
  layout, navigation, accessibility, and replay controls.
- **Existing Playwright 1.58.0 in deployment CI**: real-browser screenshots
  after the deployed page confirms the exact expected revision.
- **Existing Vitest + TypeScript + Biome**: deterministic conversion/geometry
  unit tests, strict type-checking, formatting and lint.
- **Existing npm lockfile**: reproducible `npm ci` without dynamic dependency
  resolution during build/deployment.

Do not add physics engines, GIS mapping packages, generic component UI kits,
paid model endpoints, or runtime asset CDNs without a concrete need and review.

## Rendering contract

The backend is authoritative for `MatchEvent`, event timestamps, actor IDs,
and optional locations. Render a canonical 105 × 68 m field in meters,
mapping the pitch X/Y plane into world coordinates using **one shared,
unit-tested transformation**. Preserve replay event selection and
time-bounded visibility. Do not invent tracked player positions, team
formations, scorer identities, fixture branding, a match score, or media.

Only the **active event actor** may be positioned using a valid recorded
`MatchEvent.location`. Never synthesize teammates, opposition, goalkeepers,
formation shapes, actor positions between two recorded events, or movement paths.
Additional players may be shown only when genuine per-player spatial data
for that match time exists in the validated source schema; the current schema
does not provide it. A source event's optional destination supports only an
event-specific directional arrow, not an inferred player route or tracked ball
path. In particular, do not place a ball at any arbitrary offset from the
active actor: the present event schema lacks an independent ball coordinate.

Synthetic scenario records remain explicitly **synthetic source records**, not
real-match tracking. The 3D avatar is a presentation of a single recorded
event position, not an assertion about an actual athlete's pose or uniform.

Use a top-down broadcast camera by default; allow subtle perspective,
depth, player silhouettes, shadows, realistic grass and lighting without
moving event locations. Keep labels, controls, and accessible information
in ordinary React HTML above/around the WebGL surface. Provide a fallback
visualization when WebGL is unavailable.

## Performance and visual acceptance

Cap device pixel ratio for mobile, avoid rendering in hidden tabs, and respect
reduced-motion preferences. Keep stadium imagery low-cost and locally owned;
review licensing for any recognizable football photography, kits or crests.
Do not encode the reference screenshot itself as a fake interactive pitch.

Acceptance requires desktop and mobile screenshots from the **verified exact
deployed SHA** compared with the approved Application Preview. Passing CI
and revision checks is necessary but never sufficient evidence of fidelity.

## Position provenance and 22-player limitation

A replay event contains the reported action actor coordinate, **not an observed
22-player tracking snapshot**. Fictional roster identities or nominal lineup
metadata are not a substitute for timestamped positions. Do not distribute
generated 4-3-3 slots or extrapolate static players as if they were observed.
Until an independently verified, time-aligned multi-player source (such as a
StatsBomb 360 freeze-frame) is ingested, show only the event's known actor,
or no player when no coordinate is available. A freeze-frame may legitimately
contain fewer than 22 visible players: preserve its actual membership and
coverage, rather than padding missing players. Its source identifiers, time,
coordinate system, and availability must remain auditable.

The replay cursor is the single time boundary shared by pitch, tactical cards,
evidence, and narrative. Snapshot and SSE payload IDs must agree. Seek/rewind
must not expose events or insights from a future cursor, and synthetic event
coordinates must never be identified as real-match player tracking.
