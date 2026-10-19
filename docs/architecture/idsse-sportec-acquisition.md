# IDSSE / Sportec — pinned historical match acquisition (Issue #134)

**Status: selected source and offline verification code; original tracking
bytes not yet examined in this runtime. No new public replay.**

### Decision and source rights

Replace Metrica as the primary candidate for authentic 11v11 motion with
the **IDSSE/Sportec Open Dataset**. The research authors explicitly state
DFL authorization and **CC BY 4.0** licensing. The selected source match
is **J03WMX — 1. FC Köln vs FC Bayern München**, Bundesliga 2022/23,
with official metadata, event data, and TRACAB observed player/ball tracking
at a published nominal 25 Hz.

Official research repository:
https://github.com/spoho-datascience/idsse-data

Original archive:
https://doi.org/10.6084/m9.figshare.28196177

Open mirror: https://huggingface.co/datasets/pysport/idsse-data

Published research reference: Bassek, M., Rein, R., Weber, H. and
Memmert, D. (2025). *An integrated dataset of spatiotemporal and
event data in elite soccer*, Scientific Data 12, article 195.
https://doi.org/10.1038/s41597-025-04505-y

**Mandatory attribution for any reuse:** credit Deutsche Fußball Liga
(DFL), cite the publication, link to CC BY 4.0, and indicate whether
the data were transformed. Tracking rights do not automatically license
original TV footage, broadcast music, photographs, third-party logos
or brand artwork. Production release/asset attribution is a separate
technical approval step even though dataset reuse is licensed.

### Pinned data source (reviewed 19 Oct 2026)

The selected PySport mirror revision is
`a715a38dfbaf5f58e431727c2b78d174101a703c`.
The authentic dataset filenames for match J03WMX are:

| Source | Original filename |
|---|---|
| Metadata | `DFL_02_01_matchinformation_DFL-COM-000001_DFL-MAT-J03WMX.xml` |
| Events | `DFL_03_02_events_raw_DFL-COM-000001_DFL-MAT-J03WMX.xml` |
| Tracking | `DFL_04_03_positions_raw_observed_DFL-COM-000001_DFL-MAT-J03WMX.xml` |

**Original tracking file**: approx. **419 MB**; the mirror's published
SHA-256 is:

```text
d3dd92e509421a6466acb0a083c009035f1751bc5fd9ef42ffa8f20d01cf7d49
```

The auditor hard-pins the full revision and that original tracking
SHA-256. This guards against treating locally manufactured positions as
published source bytes. For metadata and events, operators must obtain
local SHA-256 from immutable-revision downloads and report them; until
they are independently bound to upstream objects those file checks
assert local integrity only, **not authenticated upstream provenance**.
The report exposes this limitation explicitly rather than inventing
unavailable upstream checksums.

### Operator commands (offline validation, no Azure)

The files are **NOT downloaded by PR/CI**, and must not be committed.
On a developer workstation with `hf` installed (or download each
immutable `source_url` directly with `curl -fL`):

```bash
REV=a715a38dfbaf5f58e431727c2b78d174101a703c
TARGET=local-data/idsse/J03WMX
mkdir -p "$TARGET"

hf download pysport/idsse-data \
  DFL_02_01_matchinformation_DFL-COM-000001_DFL-MAT-J03WMX.xml \
  DFL_03_02_events_raw_DFL-COM-000001_DFL-MAT-J03WMX.xml \
  DFL_04_03_positions_raw_observed_DFL-COM-000001_DFL-MAT-J03WMX.xml \
  --repo-type dataset --revision "$REV" --local-dir "$TARGET"

META_SHA=$(shasum -a 256 "$TARGET/DFL_02_01_matchinformation_DFL-COM-000001_DFL-MAT-J03WMX.xml" | cut -d' ' -f1)
EVENT_SHA=$(shasum -a 256 "$TARGET/DFL_03_02_events_raw_DFL-COM-000001_DFL-MAT-J03WMX.xml" | cut -d' ' -f1)

uv run --frozen python -m pitchvolt.idsse_source_audit \
  --directory "$TARGET" \
  --metadata-sha256 "$META_SHA" \
  --events-sha256 "$EVENT_SHA" \
  --verify-tracking
```

On systems without `shasum`, use `sha256sum`. The full verification
streams the 419 MB file in chunks to avoid memory spikes. An XML parser
does **not** load that entire tracking file in this phase. The script
refuses a tracking hash mismatch; leave `--verify-tracking` out only
to inspect metadata/events **with tracking explicitly unverified**.
Never interpret an operator-chosen SHA-256 of a modified file as proof
of published source origin.

The repository's `.gitignore` already excludes `/local-data/`;
do not attach raw third-party XML to PRs, Actions artifacts or issue
comments. Safe audit output contains only metadata and aggregate flags,
not sampled coordinates, player movements or unreviewed personal data.

### What phase 1 actually checks

- Correct match directory and filenames; pinned revision URLs and
  source-published tracking fingerprint
- Metadata XML structure, match ID, official competing team names,
  player registration identities and source pitch size (105 × 68 m)
- Event XML structural well-formedness and locally checked fingerprint
- Optionally the full original tracking file SHA-256
- Explicitly **does NOT** claim frame count, 25 Hz coverage,
  all 22 players visible at each instant, successful event-frame
  synchronization, complete ball trajectory, or a ready-to-serve
  historical asset. Those are future source adapter audit results.

### Source coordinate and temporal hazards

Sportec raw tracking is pitch-centred, whereas Sportec raw event
coordinates use a different origin and vertical-axis direction. Do not
copy either directly into WebGL or onto synthetic `MatchEvent`.
Kloppy's Sportec loaders can normalize both to consistent pitch
coordinates; the next PR must validate this normalization against
known pitch corners and real source metadata **before** projecting
into the provider-neutral 105 × 68 m tracking contract.

Use event IDs / source timestamps and tracking frame IDs to establish
true joins. Nominal 25 Hz does not itself validate per-frame timing or
presence of every player/ball observation. PitchVolt must preserve
missing/off-field values, actual participant identities, ball height
when supported, substitutions and individual evidence provenance.
There must be no illustrative 4-3-3 formations, fabricated ball carrier,
possession/pressure claims based purely on proximity or synthetic
Harbor/Ridge identity mixing.

The browser should ultimately fetch one **compact, audited 20–30 s
historical segment** rather than parse a 419 MB XML original. Even an
authorized derived asset needs explicit source attribution in the
application and an approved rollout; no public serving flag is enabled
by this PR.

### Next milestones

1. Run this SHA-pinned audit on downloaded original match bytes;
   record digests, original sizes and metadata output, without
   exposing raw tracking data in CI.
2. Add an optional **pinned Kloppy** loader offline with normalized
   tracking, ball XYZ, stable frame/time identities and robust
   event-to-tracking joins; audit coverage and select a real
   20–30-second passage based on genuine events.
3. Convert exact source samples to the v1 tracking contract (extend
   only as needed for genuine ball Z, provenance and provider type).
   Preserve fail-closed missingness, never invent players.
4. Build the bounded historical segment asset with DFL attribution
   and then the separate source-backed 3D replay mode; retain
   existing controls and compare exact deployed screenshots to the
   approved PitchVolt Application Preview.

**Do not merge this PR without manager review.** Existing merge-only
Foundry smoke remains unchanged. No ad-hoc billable inference, new
Azure resources, model deployments, or production replay activation.


## Phase 2: bounded observed-frame audit and shot candidates

Implemented in `src/pitchvolt/idsse_frame_audit.py`.

Kloppy's source parser confirms that tracking XML stores a separate
`FrameSet` for each physical player/ball object, grouped by
`GameSection` (period), each containing source-numbered `Frame`
records with timestamp `T` and source-native coordinates `X`, `Y`,
and for the ball `Z`. The ball record also contains
`BallStatus` and a *team-level* `BallPossession` flag.
There is **no verified per-frame player ball-carrier** in that field.

The audit:
- refuses a production report until the original 418,524,833-byte
  tracking source matches its published fixed SHA-256;
- verifies the locally acquired match metadata and event XML with
  operator-supplied digests, and extracts registered player/team IDs
  (referee objects must not become extra field players);
- streams the complete XML using stdlib ElementTree with bounded
  memory, collecting only 2–750 selected source frame numbers from
  one explicitly selected period; no full-match positional replay
  is returned or cached;
- preserves missing ball XYZ and player positions, checks unique
  object/sample IDs, timestamp consistency among objects, 25 Hz
  timing *for the sampled frames*, and actual player coverage;
- never pads 22 players or creates a possession-holder, ball motion
  path, source event alignment, or public playback asset;
- separately lists only recorded `ShotAtGoal` events that contain
  both an actual `CalculatedFrame` and `CalculatedTimestamp`.
  Their game period remains **unknown** until separately verified;
  no inferred event tracking joins are emitted.

Run after downloading the original three files using the commands
above. The frame IDs below are **operator input examples**, not a
claim that these specific frames contain an eligible match scene:

```bash
uv run --frozen python -m pitchvolt.idsse_frame_audit \
  --directory local-data/idsse/J03WMX \
  --metadata-sha256 "$META_SHA" \
  --events-sha256 "$EVENT_SHA" \
  --period 1 \
  --first-frame 10000 \
  --frame-count 625
```

The CLI produces a privacy-safe **aggregate JSON report** including
measured counts, verified-data flags and available source-linked
shot candidate IDs. It does not output any player positions. A
valid `CalculatedFrame` is only a *candidate anchor*: validate
`GameSection`, absolute timestamp, 25 Hz and source match identity
before claiming a synchronized 20–30-second replay.

A separate, explicitly permitted `require_original_digest=False`
parameter exists for pure unit-test XML fixtures. Its reports always
state `source_tracking_sha256_verified=false` and
`public_replay_enabled=false`; it is **not exposed by the CLI**.

Source reference: PySport Kloppy's maintained Sportec XML tracking
deserializer at
https://github.com/PySport/kloppy/blob/master/kloppy/infra/serializers/tracking/sportec/deserializer.py

No new Azure resources, GitHub billable source downloads, deployment
changes or model invocations are authorized by this phase.

## Authentic J03WMX 625-frame benchmark — verified in CI, 19 October

The isolated read-only GitHub job
https://github.com/niktolis/pitchvolt-ai/actions/runs/39252710693
downloaded the **real immutable-revision tracking XML** (419 MB) and
validated its entire byte stream against the upstream-published SHA-256
`d3dd92e509421a6466acb0a083c009035f1751bc5fd9ef42ffa8f20d01cf7d49`.

The audit artifact `idsse-j03wmx-authentic-coverage` reports:

| Measured property | Genuine observed result |
|---|---|
| Match | DFL-MAT-J03WMX, source period 1 |
| Window | Source frames **10000..10624** (625 samples) |
| Registered player coverage | **22/22 at all 625 frames** |
| Independent ball XYZ | **625/625 samples**; none missing |
| Time spacing | Source frame IDs and timestamps conform to 25 Hz |
| Shot events with recorded frame anchor | **18** |
| Referee / unregistered tracking objects excluded | **3** |
| Controlling individual | **Not established** |
| Selected shot frame/event alignment | **Not established by this benchmark** |
| Authentic live replay asset | **Not yet produced** |

This is measured aggregate evidence; no player or ball coordinates were
published, and the source XML was **not** checked into Git or uploaded
as an Actions artifact.

The next isolated CI pass extends this baseline by validating a
particular genuine `ShotAtGoal` source event,
`18226500000041`, with `CalculatedFrame=12519` and
`CalculatedTimestamp=2023-05-27T15:31:53.360+02:00`.
It chooses the exact frame window beginning at
`12519 - 300 = 12219`, then checks the event timestamp directly against
the observed original ball frame `T` (5 ms max difference).
Unlike a nearest-frame guess, failure rejects the segment. The chosen
scene only becomes admissible for replay **if** both the independently
verified full source and its observed 22-player/ball coverage pass.

The workflow's source downloads are fixed to the immutable mirror
revision and run with read-only repository permissions. Only a small
audit JSON report is retained briefly; no Foundry inference, Azure
deployment or custom paid resources are invoked.
