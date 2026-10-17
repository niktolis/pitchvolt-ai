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

A player model can depict the source-backed active event actor. Additional
players require independently sourced tracking/formation information;
otherwise use an explicitly labeled illustrative scene, never fictional
data masquerading as observation.

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
