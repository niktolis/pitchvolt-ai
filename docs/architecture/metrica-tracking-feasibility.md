# Metrica synchronized tracking — offline feasibility gate (Issue #134)

**Status: source format identified; public redistribution **NOT AUTHORIZED**.**
This is a research/developer audit, not a production data ingress,
not a source grant, and not the implementation of the source-backed
22-player/ball broadcast UI.

## Upstream evidence (verified 19 October 2026)

- Repository: https://github.com/metrica-sports/sample-data
- Pinned upstream commit: `e706dd506b360d69d9d123d5b8026e7294b13996`.
- README: anonymized samples; normalized [0,1] pitch coordinates, (0,0)
  top left, (1,1) bottom right, 105 × 68 m pitch, synchronized events and
  tracking data. The upstream explicitly requests attribution for public use.
- Games 1 and 2 have event CSV files, plus **separate Home and Away team
  tracking CSV files**. Games 1/2 event CSV headers include `Start Frame`,
  `Start Time [s]`, `From`, `To`, action start/end coordinates.
  Tracking CSVs have three metadata/header rows, source player slots and
  a Ball x/y pair. Metrica CSV readers use 25 Hz / 0.04-second sampling.
- Game 3 is a **different EPTS/FIFA representation**, JSON events + XML
  metadata + tracking text; it requires a separate format adapter.
- The upstream tree has **no LICENSE file** and GitHub reports
  `license: null`. Attribution guidance does **not** establish public
  hosting/redistribution rights. Written permission or a clear applicable
  license must be verified before storing source data in the repository,
  sending it to Azure, distributing derived sampled trajectories or serving
  a historical replay to users. Inspect legal terms as applicable.

References: upstream README, the pinned GitHub source paths, and
`kloppy` Metrica loader documentation:
https://kloppy.pysport.org/user-guide/loading-data/metrica .

### Data boundary

The new `pitchvolt.metrica_offline_audit` has **no network API**. It
operates on preexisting, locally controlled files under a folder named
`Sample_Game_1` or `Sample_Game_2`, and requires the exact SHA-256 of
each original Home, Away and Events file. It refuses mixed game
names, mismatched file hashes, inconsistent Home/Away frame timestamps,
an unrecognized header, invalid x/y pairs, and unbounded sample counts.

Only three CSV filenames are supported for each match:
`Sample_Game_N_RawTrackingData_Home_Team.csv`,
`Sample_Game_N_RawTrackingData_Away_Team.csv`, and
`Sample_Game_N_RawEventsData.csv`.

The output is **aggregate metadata only**: number of player slots,
valid/unknown/out-of-field samples, observed ball x/y pairs, frame count,
source revision, verified digest, and source-event/tracking frame joins.
Both `may_publish_source_data` and `may_serve_tracking_replay` remain
**false**, regardless of coverage. No raw player/ball locations are
logged, cached, uploaded, hosted, or checked into Git.

### Operator-run offline audit (not required for CI)

Place only authorized locally obtained files under ignored
`local-data/metrica/Sample_Game_1/`, and compute each SHA-256 independently.
From the repo root:

```sh
uv run --frozen python -m pitchvolt.metrica_offline_audit \
  --directory local-data/metrica/Sample_Game_1 \
  --game 1 \
  --commit e706dd506b360d69d9d123d5b8026e7294b13996 \
  --home-sha256 <actual-full-sha256> \
  --away-sha256 <actual-full-sha256> \
  --events-sha256 <actual-full-sha256> \
  --max-frames 250
```

The SHA-256 values are **not supplied or guessed** in this repository.
Actual original files have **not** been run through the parser here;
they were not available for local examination. All CI tests generate
small, original synthetic CSV files exclusively to exercise the boundary.
Audit results must be reviewed before any separate licensed
tracking-data ingest is implemented.

### Source–event join and ball/possession semantics

- Both teams must have matching `(period, frame, time_seconds)` samples.
  The expected sampling rate is 25 Hz, but this is verified only against
  the inspected samples. Frame-index event joins are counted; a sample
  with zero event matches is **not** deemed event-aligned.
- Source CSV player slots have **anonymized identifiers**, not surnames or
  official logos. Metadata may include substitutes and absent samples;
  no 11/11 or 22/22 coverage guarantee is implied.
- Ball x/y **channels exist**; availability and reliability must be
  audited, including missing or out-of-field coordinates. The ball
  position does **not** automatically identify a controlling player or
  whether a challenge is underway.
- Pressure, duel and possession-holder attribution require explicit
  source event/metadata or a separately evaluated model. Never
  derive a contested state from proximity alone without marking it
  as inference and validating it first.
- Never join an anonymized Metrica match to the Harbor FC/Ridge FC
  synthetic fixture or to unrelated StatsBomb 360 event frames.
- No interpolation/forward fill before proving source frame timing,
  missingness semantics and a dedicated approved rendering policy.

## Engineering sequence

1. **This PR** — reproducible offline format/provenance audit, license
   gate, synthetic regression tests. No production API or cloud change.
2. Obtain **written data-use approval** for public visualization/hosting,
   or select an explicitly licensed substitute source.
3. Read source-pinned Game 1/2 files offline, publish a reviewed **only
   aggregate** report and confirm exact ball/player coverage/frame joins.
4. In a separate PR, implement a versioned provider-neutral observed
   spatiotemporal schema (player samples, ball samples, team, identity,
   frame/time, source URI/digests, missingness, optional contest state).
5. In an explicitly separated **historical game** mode, render only
   original time-aligned samples, camera ROI and observed players/ball.
   No fabricated movements or synthetic-match mixing.
6. Require exact-deployment-SHA screenshot comparison against the
   approved PitchVolt Application Preview and full CI/performance checks.

Preserve the existing merge-only Foundry smoke authorization and do not
run new paid inference or provision new Azure resources in this work.
