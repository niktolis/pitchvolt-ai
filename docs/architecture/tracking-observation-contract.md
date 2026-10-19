# Versioned source-observed player/ball contract (Issue #134, phase B)

**Status: v1 schema plus one read-only StatsBomb 360 projection; no tracking
source is redistributed, hosted, or used by the production web application.**
No new Azure resources and no inference calls are needed for this change.

Implementation: `src/pitchvolt/tracking_contract.py`, tests:
`tests/test_tracking_contract.py`.

## Why a separate contract

The existing `MatchEvent` and `ReplayDataset` are authoritative for
**synthetic** actions; they cannot truthfully represent continuous 22-player
tracking or an independently observed ball. StatsBomb 360 supports
**event-exact camera-visible frozen observations**, and Metrica's
anonymized Game 1/2 CSVs describe **time-sampled** Home/Away + ball
channels. Their temporal semantics differ. The contract does not convert
one to the other or mix matches. It defines immutable, provider-neutral
Pydantic objects; the first separate source adapter is documented below.

## Structured v1 model

| Object | Contract | Evidence safeguard |
|---|---|---|
| `TrackingManifest` | Schema version 1, historical provider/match, capture mode, source revision, file SHA-256 fingerprints, rights status | Reject duplicate source types; Metrica requires Home+Away+Events at immutable commit, 360 requires Events+FreezeFrames; no public-serving flag can be enabled |
| `TrackingSnapshot` | One exact frame/event observation, source record identifier, period, source frame or event ID, clock milliseconds | Match ID bound to manifest, ordered sample chronology, source ID uniqueness (two distinct events may share a timestamp), at most 22 **observed** detections (not a 22-player guarantee) |
| `PlayerObservation` | One source detection, optional *real* identity/team, keeper flag, observed location | Anonymous detection remains anonymous; no inferred persistent identity across frames, no duplicate detected ID or identified player per frame; up to 11 identified team detections per side |
| `ObservedLocation` | `observed_on_pitch`, `observed_outside_pitch`, `missing` | Source-native coordinate retained and transformed into 105 × 68 m `Point` **only** if in bounds; no clamping, synthetic defaults or forward fill; source-to-pitch coordinates must match exactly within numeric tolerance |
| `PossessionObservation` | Unknown, explicitly source-reported controlled or contested | Unknown has no carrier/team, reported state requires explicit source-evidence IDs, contested observations cannot assign a player holder |
| `TrackingSequence` | Immutable sequence of exact source snapshots | Continuous samples can be requested only at an exact `(period, clock_ms)`; freeze frames only by the exact source event ID. Missing lookup returns `None`, never a previously or subsequently observed player/ball |

Coordinates are stored **twice by intent**, to permit auditing: raw
coordinates with source units `normalized_0_1`,
`statsbomb_120x80`, or `pitch_meters`, and a provider-neutral
`Point(x_m, y_m)` represented in the existing canonical
`105 × 68` pitch domain. The source-to-meters conversion is checked
by the validator, with a sub-micrometre absolute tolerance matching
the existing six-decimal StatsBomb source normalizer. Out-of-field raw observations remain available for
diagnostics, with no renderable `pitch` position. Missing observations
have neither raw nor pitch coordinates; the ball has its own required
location (which can be explicitly missing) rather than being offset
from an observed event actor.

## Temporal and source isolation

- **Continuous**: a source frame number is mandatory, event UUID is
  forbidden, and the exact `(period, clock_ms)` must exist for lookup.
  No nearest-time, interpolation, extrapolation, or carry-forward.
- **Event-exact**: a source event identifier is mandatory, source frame
  is forbidden, and only `at_event(source_event_id)` is available.
  Sparse StatsBomb freeze frames do **not** imply continuous motion.
- All source snapshots must reference the **same match** as the
  manifest, be time-ordered (event freeze frames may share an exact clock), and contain distinct source
  detection identities. Do not splice the Metrica sample game into
  Harbor/Ridge fictional replay or an unrelated StatsBomb historical
  match. This contract does not add a combined API or enable either
  historical source in production.
- **Coverage:** a declared detection with an explicitly missing
  location remains missing. A missing detection is not instantiated
  as a roster/formation player. A source frame with 9 observations
  means 9, not 22.
- **Rights:** source provenance proves *which bytes*, not permission
  to distribute them. `rights_status=unverified` is the default;
  an asserted authorization requires external documentary evidence,
  but is not itself a license. Both `serving_enabled` and
  `public_replay_enabled` are **schema-enforced false** for v1.
  A future reviewed release and independent legal grant would be
  necessary to enable actual public use.

## Explicit non-deliverables of this PR

No Metrica source-file fetching/embedding, no continuous player/ball
adapter, no web/SSE endpoint, no 3D player movement and no inference
on ball possession from proximity. Actual 30+ MB Metrica CSV files
remain untested against the provisional offline audit until authorized
original-file inspection is available. Passing unit tests does NOT
prove licensed, 22-player, end-to-end historical replay.

## Next review gate

1. Confirm independently documented historical source redistribution
   and derived playback rights, or identify a licensed alternative.
2. Review an original-file, SHA- and Git-pinned offline audit with
   real per-team player and ball coverage, time synchronization, and
   null rates. Do not invent missing values.
3. Build one independently tested source-specific adapter that returns
   this contract only from authenticated/approved original source
   observations. Enforce source frame/event joins and provenance pins.
4. Add historical replay mode and browser visualization **only after**
   licensing and demonstrated time alignment. Keep synthetic and
   StatsBomb 360 modes distinct and retain exact-seek behavior.
5. Compare browser visuals against the approved 1672 × 941 preview
   at the exact deployed commit. Automatic tests alone do not prove
   visual acceptance.

See [offline Metrica feasibility](metrica-tracking-feasibility.md)
and [rendering constraints](pitch-rendering.md).

## First offline source adapter: StatsBomb 360 event freezes (19 October 2026)

Implementation: `src/pitchvolt/providers/statsbomb_360_tracking.py`,
regressions: `tests/test_statsbomb_360_tracking.py`.

The existing original-file loaders require independently provided SHA-256
fingerprints and verify each original source event and 360 freeze frame.
This read-only projection uses only their previously validated results.
It requires an official commit-pinned StatsBomb Open Data event URL
and a separately supplied official 360 source URL with **the same
revision and match**. A pinned URL does not independently prove
that file exists in the public upstream or grant redistribution rights.

Each camera observation retains its source-native 120×80 coordinate
and auditable canonical 105×68 position. Real off-pitch measurements
remain unrenderable rather than clamped to a fake field edge.
Only the original event actor retains a persistent source player ID;
teammates may keep the event team ID; opposition detection team IDs
are deliberately **unknown** without an independently verified mapping.
A unique detection ID is **event-scoped**, not a persistent roster identity.

The 360 format has **no independently observed ball position channel**.
Every projected snapshot therefore has an explicitly **missing ball**
and **unknown possession**. No controlling player, challenge, duel,
or ball position is inferred from an actor, event or proximity.

Only exact-event lookup is permitted. Different source event records
may have the same match-clock time; each remains an independent frame.
Any event without its own frame produces no new position observations.
There is no interpolated motion, API publication, historical mode,
rendering, external source-file copy, Azure deployment modification,
or Foundry model invocation. Tests use only original tiny synthetic JSON.
Both public serving switches remain enforced **false**.

This adapter is **sparse event-only historical projection**, not
continuous 11v11 player tracking, measured ball motion, or proof of
real historical replay eligibility. Authentic licensed continuous
player/ball observations remain a separate blocker.
