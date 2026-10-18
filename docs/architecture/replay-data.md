# Unified replay datasets and cursor semantics — issue #66

The `pitchvolt.replay_dataset` module provides a **single read-only
presentation interface** across synthetic fixtures and independently verified
historical StatsBomb files. It is not a generalized import into the
`MatchProcessor` and does not relax the synthetic-only `MatchEvent` model.

## Source-specific loading, source-neutral query

- `SyntheticReplaySource(name, seed).load()`: delegates to the existing
  canonical `scenario` registry, validates `MatchEvent`, and preserves all
  actor/event IDs and pitch positions. An SHA-256 fingerprint covers the exact
  deterministic serialized ordered event records. Short six-event fixtures are
  declared **excerpts**; only the deliberately regulation-clock-spanning
  `extended_match` is marked `full_match`. These are fictional records,
  not football-realistic calibrated telemetry.
- `HistoricalReplaySource(verified_fixture).load()`: accepts only a
  `HistoricalFixture` obtained through independently pinned/checksum-verified
  original event acquisition. It reuses
  `project_historical_actions` (known Pass, Carry, Pressure and Shot).
  Unsupported/unlocated event types are counted explicitly; source match ID,
  origin, event SHA and URL remain unchanged. Historical player/team *names*
  are display labels, **not synthetic IDs**. Source actor positions alone are
  shown; no trajectory, lineup, scoring or teammate position is invented.
- Both return a frozen `ReplayDataset` with `manifest`,
  `actions`, `projected_count`, omission counts, and `at_cursor(ms)`.
  Only synthetic datasets carry `canonical_match` and
  `canonical_events` and permit deterministic tactical analysis.
  **Historical Open Data never passes through `MatchProcessor`.**

## Temporal contract

`at_cursor(ms)` binary-searches the ordered source event clock; it returns
the latest recorded **event**, its original timestamp and whether an
observation occurred at that *exact* cursor. An actor returned from a previous
event is a historical selection, **not a tracked position at the new time**.
Before the first action it returns no event. Same-clock actions are ordered by
source index, and period/clock regressions fail closed. It never predicts a
position between events. Visual consumers must hide/scope stale positions
and narrative/evidence at the authoritative cursor.

A dataset's `manifest.event_count` is **the number of original input
events**. `projected_count` may be lower for historical inputs with
unsupported or unlocated actions. A historical file declared `full_match`
is not proof that our projector covers all event families.

## Compatibility and scope

The existing `/api/matches/{name}/{timeline,state,stream,evidence}` routes
still expose only the validated synthetic registry and preserve their JSON
and SSE contracts. The initial integration makes the server's `_load`
resolve the shared synthetic loader; this PR intentionally does **not**
publish historical records, 360 frames or new API schemas.
There is **no** new Azure resource, model invocation or live source download.

The next bundle under #66/#59/#60 should introduce validated
source-authoritative fixture presentation (team side, roster and event-sourced
score/substitution state), and only then expose a versioned client contract
with generated OpenAPI TypeScript. The historical source needs independent
license/attribution review and a separate approved transport before use
in the hosted app. The frozen current `MatchEvent` event family remains too
narrow for faithful historical substitution/score semantics.

Acceptance: all scenario registry contracts unchanged; golden stable digest
per seed; strict source ID and SHA provenance; backwards seeks and sparse
period/event clocks; explicit historical omissions; no inflated 22-player
tracking or score claim; Python, frontend and D2 CI green.
