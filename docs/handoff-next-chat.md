# 19 October — genuine IDSSE 22-player 3D historical replay (Issue #153)

PR #152 merged as eec040d387b48b3cb174e64925b46b481a7c5e24;
Python/frontend/diagrams and Foundry merge-only smoke passed. Azure
deployment status should be independently verified before declaring
release green.

New independent PR (Issue #153) includes 25-second authentic clip
from original verified J03WMX DFL IDSE/Sportec source,
625 frames/22 players + ball XYZ at 25 Hz, source event
18226500000041 frame 12519. CC BY4.0/source attribution retained.
Web asset exact SHA-256 d1b6dda14d84a266cd26ef607c12b62712fe906a8de9c9b75be860b464346db6,
and file size 381441 bytes. A branch-limited workflow validates and
commits the exact reviewed asset from prior authenticated Actions
without carrying original 419MB XML or relying on expiring artifact
at runtime. No invented player/ball positions or ball carrier.

New historical mode in same approved broadcast shell: observed XY
for all players, measured ball Z, under-pitch exact source-frame
playback controls, source-only shot/key moment, DFL attribution.
Synthetic/Foundry mode accessible separately and unchanged.
No Azure resources or ad hoc inference, manager must approve merge.
Future visual acceptance demands a *post-deployment* screenshot
matched against 1672x941 approved preview. See
docs/architecture/historical-source-replay.md.

---


# 19 October — Issue #150, authentic observed 25-second clip encoder

**Merged PR #146**: commit cb5d897592c749d322aa3f3ce77f051a717a4ea1,
merge-only Foundry smoke and Python/frontend/architecture passed.
New standalone Issue #150 branch feat/150-idsse-source-backed-clip-export
adds deterministic offline Sportec player XY + ball XYZ encoding from
full SHA-pinned original source; source event 18226500000041, frame
12519, period 1, frames 12219..12843 (625 samples, 25 Hz).
Output stores source identities, frame IDs, timestamps, true source
status, DFL/CC-BY-4.0 attribution and verified hashes. A strict decoder
rejects null/fabricated samples, skipped frame IDs and timestamp drift.
An isolated read-only GitHub workflow exports only the compact
derived asset and aggregate SHA report as a seven-day artifact.
No original ~419MB XML committed, no production hosting, no inferred
player carrier, no Azure/Foundry changes. Synthetic unit tests are
not substitutes for the authentic workflow acceptance.

Next after **manager approval** of this PR: review/download the real
asset and implement a separately approved Three.js historical replay
mode with all 22 source-backed moving players, moving ball and existing
replay controls. Compare deployed UI to branding preview. Preserve
independent UI work and the source data CC BY/DFL attributions.

---

# 19 October: IDSSE authentic source-window inspection milestone

PR #144 was explicitly approved and merged into main at
8553bc11e21697182c923c22de13daee69f6d7be.
Separate UI PR #143 also merged afterward at
808215a495f9e79af3ca8414c919d90640858334;
tracking development is based on this newer main.

**Critical CI incident:** post-merge #144 and #143 actions (Python,
frontend, D2, production deploy and Foundry merge-only smoke) failed
within 2–3 seconds each with **zero recorded steps**, and GitHub job log
download returns 404 BlobNotFound. This is not established as a
source-code failure; investigate GitHub Actions billing/runner capacity,
repo/account policy and GitHub status before retrying. Do NOT retry
the billable Foundry smoke without explicit new authorization; no
actual model execution is evidenced by those zero-step jobs. Last
confirmed successful prod rollout precedes these merges.

New separate PR after #144: an offline bounded Sportec FrameSet parser,
actual ball XYZ and player coverage counters, time/detection integrity,
registered roster filtering, and source `ShotAtGoal` candidates with
explicit recorded CalculatedFrame. Full real tracking SHA required by
the CLI. Unit tests use ONLY authored toy XML; the 419 MB source has not
yet been downloaded and its real observations/joins remain unverified.
No production 3D replay, interpolation, public data serving or Azure
resource changes. See docs/architecture/idsse-sportec-acquisition.md.

**Manager must approve each PR merge.** Preserve the bounded
post-merge smoke policy; never initiate additional billed inference
to compensate for Actions infrastructure problems.

---

# 19 October 2026 — approved IDSSE pivot / source acquisition milestone

**Current approved direction:** technical manager accepted use of
DFL-authorized, CC BY 4.0 IDSSE/Sportec tracking for real source-backed
22-player and moving-ball replay. Earlier Metrica redistribution concerns
still apply to Metrica but are not a universal barrier to published
tracking data.

Selected historical match: J03WMX (1. FC Köln vs Bayern München),
mirror revision a715a38dfbaf5f58e431727c2b78d174101a703c.
Mirror tracking file ~419 MB, published SHA-256 pinned in
src/pitchvolt/idsse_source_audit.py. Official DFL attribution plus the
Bassek et al 2025 Scientific Data paper must be cited. First dedicated
PR adds **local-only** metadata/event XML safety/integrity checks and
full tracking digest verification; source bytes are not bundled and
actual original-file compatibility/25Hz/coverage have NOT been tested
by the assistant runtime. See
docs/architecture/idsse-sportec-acquisition.md.

Current main at kickoff: e28eac6f40963888ee3f9b593bd1c6e4f31c3ee5.
PR #140 StatsBomb 360 adapter was merged; standalone UI PRs also
merged. Preserve replay, production Foundry-disabled setup and all
visual approval criteria. This IDSSE PR does NOT enable public
historical replay, AI inference changes or extra Azure resources.
Upon CI green, request explicit manager approval to merge; the
existing single-bounded Foundry smoke remains the only authorized
post-merge inference.

Following milestone: independently verify original source bytes
locally; normalize real Sportec player/ball XYZ and event timing via
tested Kloppy adapter, audit coverage, select and render actual 20–30 s
recorded source scene without synthetic trajectories.

---

# 19 October — source-exact historical tracking after PR #139

Latest verified merge: PR #139, main commit
3fa7d684a60e2e91274a71ee2d68e50d0b257f89.
Python, frontend, architecture, Azure deployment and automated
Foundry smoke passed (run 39216369022).
Independent UI PR #138 merged afterward at main commit
946caf4c9006c3aa0160d099d17cbabac6dc2725.
Keep both streams intact; recheck live main before every change.

Next separate Issue #134 PR: offline source-exact StatsBomb 360
camera freeze-frame projection into the approved versioned tracking
contract. Existing SHA-checked historical source loaders feed
the adapter; source event ID, period, clock and team are revalidated.
Camera-visible actor and anonymous detections retain measured positions.
Ball location and player possession remain explicitly unknown.
Nothing is interpolated, fabricated, publicly hosted, or joined
to fictional Harbor/Ridge. No extra Azure resources or model inference.

See docs/architecture/tracking-observation-contract.md.
Manager approval is required for the PR merge. Only that reviewed
merge triggers the standing-authorized bounded Foundry smoke.
The critical remaining dependency for continuous 22-player+ball
broadcast rendering is lawful source rights and original-file coverage.

---

# 19 October — verified Foundry CI and source-neutral tracking contract

**Authoritative newest checkpoint (older notes below are historical).**
PR #136 merged on main `37de0d762f7fdb1df37509c4a55ddcbd4dd45a5c`.
The merge-only [Foundry smoke 39214473549](https://github.com/niktolis/pitchvolt-ai/actions/runs/39214473549)
and Python/frontend/diagram checks passed. At the first review,
production deployment was still running; recheck its final result.
No new Azure identity setup or macOS inference is needed.

**Current dedicated PR:** Issue #134 source-neutral observed tracking
contract. Independent, immutable Pydantic v1 schema for continuous
player/ball samples and sparse event-exact 360 freeze frames, with
raw-to-105x68 source position checking, explicit unknown/outside-pitch
values, typed source-reported possession, strict match/temporal
identity, and both public serving switches permanently false in v1.
Only original synthetic unit-test observations; no actual Metrica
bytes or hosted API. Do NOT invent 22-player formations, missing
ball motion, synthetic/historical cross-match links, or publish
source data without independently confirmed permission.

See `docs/architecture/tracking-observation-contract.md`.
This PR must pass all offline CI and **manager review before merge**;
each approved merge still triggers the bounded Foundry smoke with no
separate approval. Next project blocker: source data licensing and
real-file audit, then independently reviewed source adapters.

---

# 19 October: first authenticated merged-PR Foundry smoke and fix

**Current facts supersede older milestone A notes below.** PR #130
is merged (`eb6f4299ebd4aa9c2679fc998bd6f74df62e4a80`).
Azure operator verified both immutable OIDC federations on the existing
CI app (main branch + `:pull_request`), Reader account RBAC and Foundry
User project RBAC.

PR #135 post-merge Foundry smoke:
https://github.com/niktolis/pitchvolt-ai/actions/runs/39211398821
OIDC + deployment check **PASS**, Analyst **11.57s**, Storyteller
**3.08s**, six source evidence calls, typed decisions, deterministic
verifier `publish` and `source=controlled` **PASS**. Overall job
**FAIL** solely due to missing optional model-authored shadow text and
assessment. No untrusted text was published; token usage unknown.
This dedicated follow-up PR corrects the overly strict acceptance
gate and stale OIDC documentation; it does not change production
inference, role budgets, resource provisioning or the merge-only trigger.

No operator PC smoke, retries, or per-run consent. Technical manager
must explicitly approve any PR merge. Keep source-backed historical
tracking Issue #134 as a separate workstream.

---

# Foundry merge automation checkpoint — 19 October 2026

**CURRENT POLICY OVERRIDES HISTORICAL OPERATOR STOP NOTES BELOW.**
PR #130 was subsequently merged. The technical manager has standing-authorized one
billable Analyst → Storyteller → deterministic Verifier smoke test **after
each PR is reviewed and merged into `main`**. New
`.github/workflows/foundry-merge-smoke.yml` uses
`pull_request_target: closed` plus `merged=true`, checks out the
trusted merge commit, reuses existing GitHub Azure OIDC vars, verifies
existing subscription and two deployments, runs the canonical CLI once,
and attaches sanitized 7-day JSON / GitHub job summary. No `push`,
`workflow_dispatch`, cron, PR-sync or automatic reruns. The project
retains deterministic public SSE with Foundry disabled. New resources
and broader paid inference still require explicit approval.

18 October live evidence: user executed
`pitchvolt.foundry_smoke --execute --acknowledge-billable-inference`
on the authentic Foundry project and **PASS** was returned: six exact
read-only tool calls, typed Analyst + Storyteller decisions,
`fact_order=[team,tactic,transition,actions]`, verified controlled
publication; Analyst ~14.93 s, Storyteller ~3.84 s. Original model prose
was unverified/shadow-only; usage counters were null/unknown.
This is live proof for **one synthetic insight**, not generalized semantic
LLM publication approval.

**One-time dependency:** existing production GitHub CI Entra principal
is documented as lacking Foundry access; an Azure administrator must verify
or assign **Foundry User** on the existing Foundry project once. This
assistant's GitHub tools cannot apply Azure IAM. If OIDC or inference
RBAC fails in the first automated run, read the CI job and fix IAM without
creating new resources. Verify trial spending limit remains enabled.

The operator's Mac regenerated `deployment.svg` with a small
cross-platform D2/font-layout difference (5516 vs 5499 view width and
embedded font changes). Do not apply that local SVG diff to the PR:
Linux D2 CI remains authoritative pending a deterministic cross-platform
rendering fix.

Read `docs/architecture/foundry-smoke-test.md`,
`docs/github-azure-oidc.md`, and `docs/judging-traceability.md`.
No PR merge without manager approval; preserve independent UI work.

---

# PitchVolt AI — authoritative project and next-chat handover

**Updated:** 18 October 2026, after PR #125 and #128 merges and during #4 Foundry milestone A/B preparation.
**Deadline:** 27 October 2026.
**Repository:** https://github.com/niktolis/pitchvolt-ai
**Project board:** https://github.com/users/niktolis/projects/6
**Production:** https://pitchvolt.app
**Separate visual/UI handover:** [handoff-ui-next-chat.md](handoff-ui-next-chat.md)

**Continuation rule:** Before doing work, read **both** handovers, then query
live GitHub `main`, open PRs/issues and deployment runs. The commit and PR
status below are a dated verification snapshot. **Refresh this document after
every significant PR**, including the exact merge SHA, CI evidence, remaining
risk and next task. Do not repeat completed work because an older chat says
otherwise.

## Confirmed engineering baseline

| Delivery | Evidence | Meaning |
| --- | --- | --- |
| Renamed PitchVolt repo and Azure OIDC | PR #112, Entra `pitchvolt-main` | Repo name is `pitchvolt-ai`; legacy Azure resource names intentionally remain |
| CI modernization | PR #115, merge `6f7536530effe1646cc8ee2beba9229d17991bdc` | Node 26.10.0, Node 24-compatible Actions, Ubuntu 24.04; no automatic screenshot job |
| Source-neutral replay boundary | PR #116, merge `a5dc8e09cdad6c24c4fcd2c89904a1db3de5d3ef` | Immutable replay dataset, canonical synthetic vs historical provenance separation, source-exact cursor |
| Source-backed multi-insight UI | PR #117, merge `bc18c9a7e7939181bd3cb08067556fc532f793d4` | Up to three *actual* published tactical insights; exact event-actor position and recorded-clock WebGL label |
| UI-specific handover | PR #119, merge `681041c419c258215e14f1512ef5e76c9200e279` | Separate visual design target and UI technical continuity; preserves agreed layout |
| **Fictional team/score/roster presentation** | **PR #118, merge `7baaa658ea9a1c8dfa0bafdd2e8e2161f615d1e7`** | Explicit fictional roster identity, match presentation API, goals-only score ledger, authored substitutions, seekable lineup |
| Cursor-safe evidence navigation | PR #121, merge `b32bea425b55bef038a3a47c124802e7527e40e5` | Async evidence response guard and latest visible insight navigation |
| Cursor-synchronized observed actor | PR #123, merge `c0bc2fc3eb25a412da90417f2396ab0d8aaa01d8` | Stop manual inspected actor from persisting after the canonical cursor advances |

**Production:** Post-#118 deployment
[GitHub run #39157651098](https://github.com/niktolis/pitchvolt-ai/actions/runs/39157651098)
**completed successfully**, both `verify` and `build-deploy`; exact revision
and public health gates remain part of the workflow. This is **not** human
approval of screenshot/visual parity. The main branch after #118 was
`7baaa658ea9a1c8dfa0bafdd2e8e2161f615d1e7`.

Backend Python/FastAPI/Pydantic, React 19 / TypeScript / Vite /
Three.js / React Three Fiber / Drei, Dockerized existing Azure Container App.
Synthetic `extended_match` has **220 fictional source actions** over two
halves, four deterministic tactical insights (two high-press, one sustained
possession, one counterattack), one authored canonical `GOAL`, and two
explicit author-declared fixture substitutions. It is not a statistically
realistic 90-minute real-football tracking feed.

## PR #118 details — DONE, do not recreate

**Backend:** `src/pitchvolt/presentation.py`, `extended_fixtures.py`,
`api.py`, `tests/test_presentation.py`. GET
`/api/matches/{name}/presentation` returns typed fictional team identities,
names, colors, text-only emblem abbreviations, coaches, 14-player rosters,
and (only when explicitly authored) starting XI. Goal ledger is built solely
from canonical `GOAL` events. 0–0 is an authored starting fact for
`extended_match`; shorter second-half **excerpts have UNKNOWN score and
UNKNOWN starters**. Two explicitly authored 61'/65' substitutions alter
active-player IDs for the extended fixture; **do not** infer substitute
players from actor changes.

**Web:** Generated `web/openapi.json` ↔
`web/src/api/generated.ts`, `web/src/api/client.ts`,
`web/src/domain/fixturePresentation.ts`, `web/src/App.tsx`,
`Pitch.tsx`, `BroadcastPitchScene.tsx`, and seek/rewind regression tests.
Scoreboard uses backend-authored snapshots at the single replay clock.
Text-only team shields use separately authored colors; the collapsible
roster shows active starters/substitution transitions. The source-actor WebGL
label uses the authored fictional surname, **not jersey-ID parsing**.
PR #117's verified multi-insight feed was preserved during conflict
resolution; no 22-player locations were added.

**Pre-merge CI:** Exact PR #118 head `4fa4d53e211658e98d7e4a9ada2e6b57031f6989`
passed Python, frontend (including TypeScript/OpenAPI/Biome), and D2
architecture checks. Previous 273 Python tests passed, 1 skipped. CI
ran again on merged main and succeeded. Temporary CI formatter and contract
extraction steps were removed before merging.

**Unfinished within #59/#60:** Original designer-approved crest artwork is
not present; only **text emblems**. Substitutions are separate authored
presentation facts, **not** an event family integrated into
`MatchEvent`/SSE. Historical source-independent lineup and score coverage
still needs rights/contract review. Mark these as partial delivery rather
than implying full professional match-tracking support.

## Concurrent work — coordinate rather than overwrite

- **PR #120 merged** as
  `78983af32d11176134d4a9b2bc1851d662b2882c`
  (source-event timeline accessibility under the pitch).
  https://github.com/niktolis/pitchvolt-ai/pull/120
- **PR #121 merged** `b32bea425b55bef038a3a47c124802e7527e40e5`;
  stale asynchronous evidence is guarded against replay-context changes,
  and Key Moment navigation targets the latest visible analysis.
- **PR #123 merged** `c0bc2fc3eb25a412da90417f2396ab0d8aaa01d8`;
  source actor selection follows the canonical replay cursor.
- **PR #124 merged** as `1f92f4073c53116282aae1c38de495b2ef268f6d`
  after #125 began: evidence panel source-event selection now follows the
  canonical seek/inspect path. #125 preserves this change in main.
- **PR #126 merged** as `1bcd42e57b921434ba2b23eb7e258aa3f4ddf7f9`
  after #125 began: broadcast tactical pitch top-alignment UI fix. #125
  does not change layout alignment; re-verify on fresh main before merge.
- **PR #127 merged** as `de4625e01bae9f7e830d1db7be08b19eee687553`:
  source-validated actor heading in the 3D pitch. PR #125 does not edit
  geometry, actor heading, or the R3F scene; preserve this work.
- **PR #125 ready for technical-manager review**
  https://github.com/niktolis/pitchvolt-ai/pull/125
  is the independent #58 source-action activity feed. It uses only
  `MatchEvent` records at/before the replay cursor, the existing event
  selection route, source status and neutral/failure outcomes. It also
  guards local narrative publication by scenario, audience, replay
  restart, and published insight time; no invented actions, positions,
  tactical insights or model text. The implementation head
  `16d373fdbef1afa784b4af62a5ca52b25eb6e2d4`
  passed 273 Python tests (1 skipped), 5 frontend test files,
  TypeScript/Biome/container build and architecture diagrams. This
  handover-only edit triggers a new CI run: verify the **latest** head
  before merge. Explicit manager approval is mandatory.
- General architecture and visual/UI implementation may advance in other
  project conversations. Never force-rewrite `main` or replay a stale
  branch over their changes. Compare file diffs, rebase with expected HEAD
  lease, preserve their features, and rerun complete checks.
- **PR #122 merged** `7f7e4f1794d04e9dc53f34e2c013e726fd13e295`;
  the general handover was synchronized after #118 and #120.
  No code or Azure configuration changed in that PR.

## Non-negotiable technical, provenance and financial rules

1. **Source-backed player positions only.** One real source-recorded
   event actor at its original event coordinate is permitted. Do not invent
   illustrated formations, 22-player XI coordinates, ball location,
   smoothed/in-between player movement, or off-field clamping. Active
   player **identity lists** are not player *positions*. Show recorded event
   timestamp separately from current replay cursor.
2. Historical StatsBomb Open Data is distinct from synthetic fixtures;
   never recast historical records as fictional canonical `MatchEvent`.
   Original offline event/lineup/360 files were SHA-verified at the pinned
   revision but are not licensed for our hosted redistribution by default.
   Match 3764440 had 4,160 events, 3,914 360 frames and **only 8** frames
   with 11+11 observed players. No continuous all-player tracking can be
   claimed. Historical original files remain offline pending legal review.
3. **Standing authorization:** one bounded real Microsoft Foundry Analyst →
   Storyteller → Verifier smoke runs unattended **after each manager-approved
   PR merges into main**. Ordinary commits and PR updates cause no billable
   smoke. Public production inference remains disabled. New resources,
   larger model workloads and removal of the trial spending limit require
   explicit approval. Budget alerts are not a hard spending cap.
4. One coherent PR at a time within a workstream; check current main and
   open PRs, preserve independent merged work, require green Python,
   frontend + generated TypeScript/OpenAPI, and D2 checks. **Ask the
   technical manager to approve a merge**; don't infer general approval
   from previous PRs. Provide a concise technical management report.
5. The approved **PitchVolt Application Preview** image is authoritative
   for UI proportions and styling. Preserve replay controls **immediately
   under the pitch**; the removed post-deployment visual-evidence CI
   job must stay removed. Verify exact deployed public commit before
   requesting the user to compare approved target and latest screenshot.
6. DRY is mandatory; one canonical provider-neutral business model,
   test-backed mappings, architecture D2 source and rendered SVGs.
   No GitHub Codex integration in corporate org `cariad-t2` without
   explicit permission. Existing Azure resource names remain unchanged.

## Operator workstation findings — October 18

- Operator confirmed PR #130 smoke `DRY_RUN` on macOS: no credential
  loading, zero inference; SDK versions found in local preflight.
- Operator Python test run: **287 passed, 1 failed** because an untracked
  obsolete pre-rebrand Python package directory exists locally. This directory is not
  in GitHub's PR branch tree. Inspect its contents and move it to a
  backup location **outside the repo** if no local modifications are
  required. Do **not** weaken the repo branding identity gate to ignore
  obsolete source trees. Re-run full checks after local cleanup.
- Operator accidentally used the **literal** Foundry project endpoint
  placeholder. Original preflight reported READY because only URL shape
  was checked. PR #130 now rejects known template markers and explicitly
  reports that endpoint existence, model deployment and Azure credits
  remain unverified. Request the **real** Foundry project endpoint from
  Microsoft Foundry project overview and validate it locally.
- Historical milestone B instruction is superseded: the 18 October Mac
  smoke **passed**; ongoing verification is the merge-only CI job. No
  operator workstation test or separate authorization is required.

## Active Foundry milestone — PR #130, not yet merged

- Current reviewed main at branch creation:
  `ae744fbc0c37c9003401228aee964e84b635905c` (merged #128).
  **PR #125 is merged** (`e340e06bbe999495f3cd1a45d7a9cf66211280b4`),
  delivering three source-event editorial activity samples and scoping
  narrative publication to replay state. **PR #128** carries a separate
  source-event-following pitch camera; preserve it.
- **PR #130** https://github.com/niktolis/pitchvolt-ai/pull/130
  branch `feat/4-foundry-offline-readiness-and-local-smoke` is the
  Foundry milestone A/B preparation. It hardens isolated smoke retry
  defaults to zero, avoids understating partial usage, records actual
  source tool calls after failures, and adds an offline
  `pitchvolt.foundry_preflight` plus fake-SDK complete two-role tests.
  Public model inference stays hard-disabled. CI, exact PR head, reviewed
  code, and documentation must be checked before merging.
- **Current automation:** One CI Foundry smoke is authorized after each
  reviewed PR merges to `main`. No billable inference runs on PR commits,
  unmerged closures or GitHub workflow reruns. CI uses Azure OIDC; operator
  PC execution is not part of the acceptance flow. A one-time Foundry User
  IAM grant for the existing CI service principal may be required.
  Merge remains manager-controlled, and no production Foundry switch
  or new Azure provisioning is authorized. See `docs/architecture/foundry-smoke-test.md`.
- Historical smoke failure: incomplete `fact_order` triggered correct
  deterministic fallback. **18 October successful smoke supersedes it**:
  all six evidence events, full four-slot `fact_order`, Analyst and
  Storyteller typed output, verifier publish, controlled source.
  Model-authored prose remains shadow-only.
- After future merge-triggered CI runs, inspect GitHub Job Summary and
  its 7-day sanitized JSON artifact for `source`, `trace`, event IDs,
  decisions, latency and optional token usage. Do not repeat failures
  automatically. No production inference switch is authorized.

## Next prioritized implementation after #118

1. **Editorial action ticker #58 (PR #125 merged)** and remaining temporal
   edge cases #63 (P0). A compact `recorded-action-feed` below the pitch
   selects the three latest **actual match_event** records at or before the
   authoritative replay cursor. It never fills gaps with fictional play,
   creates a tactical insight, or derives a ball/player trajectory. The
   existing `recentInsightsAtCursor` three-insight feed is separate.
   PR #125 is merged as `e340e06bbe999495f3cd1a45d7a9cf66211280b4`;
   the next task is offline Foundry #4, followed by judge-ready replay
   end-to-end tests. Keep the UI-specific handover independently current.
2. **Original fixture crest/artwork and UI target fidelity #59/#18/#61.**
   Extend only after approved visuals, real production screenshot and
   existing source identity contract. Avoid celebrity/real club
   copyrighted assets and invented photos, formations or players.
3. **Foundry genuine two-agent verification #4 (P0).** Offline tests and
   published role/evidence tools already exist; read
   `docs/architecture/controlled-narratives.md`,
   `docs/architecture/foundry-smoke-test.md`,
   `docs/architecture/foundry-runtime-guardrails.md`. Previous smoke
   successfully exercised multiple Analyst evidence tool calls, but final
   publication historically fell back on `fact_order`, but the
   18 October end-to-end live test passed. Ongoing live acceptance is the
   standing-authorized merge-only GitHub Actions smoke; analyze its results.
4. **Hackathon submission freeze by Oct 25–27:** issues #8/#31/#6:
   measured E2E replay latency, deterministic demo, Azure operating cost
   controls, accurate architecture/judging traceability, accessible
   responsive browser review and 60–90s video. Defer P2 multilingual,
   broad historical StatsBomb import and public Pages unless blocking.

## Repository navigation and checks

- API/domain: `src/pitchvolt/api.py`, `events.py`, `intelligence.py`,
  `replay_dataset.py`, `presentation.py`, `extended_fixtures.py`,
  `providers/statsbomb_historical.py`, `providers/statsbomb_360.py`.
- Browser: `web/src/App.tsx`, `web/src/domain/replayClock.ts`,
  `web/src/domain/editorialActivity.ts`,
  `web/src/domain/fixturePresentation.ts`, `web/src/components/Pitch.tsx`,
  `BroadcastPitchScene.tsx`, `EventTimeline.tsx`.
- Docs: `docs/architecture/README.md`,
  `docs/architecture/replay-data.md`,
  `docs/architecture/fixture-presentation.md`,
  `docs/architecture/frontend.md`,
  `docs/judging-traceability.md`, **this document** and the
  [separate UI handover](handoff-ui-next-chat.md).
- Checks: `uv sync --frozen --extra dev`,
  `uv run --frozen bash scripts/check.sh`,
  `npm ci --prefix web`,
  `uv run --frozen bash scripts/check-web.sh`,
  `bash scripts/render-architecture.sh --check`.

**Copy into a fresh project conversation:**
"Continue PitchVolt AI from `docs/handoff-next-chat.md` and
`docs/handoff-ui-next-chat.md` in `niktolis/pitchvolt-ai`.
First check actual main/CI, merged #118/#120/#121/#122/#123,
and open #124/#125 before touching UI or general handoff.
Finish PR #125 (#58) without overwriting PR #124, then
remaining #63 temporal tests and Foundry offline readiness.
Use only source-backed positions. One isolated Foundry smoke is
authorized per PR merged to main using GitHub Actions OIDC; no
operator-run local tests. No new Azure resources or larger inference
workloads without approval. Run CI and wait for merge approval."

## Latest Foundry review — 18 October 2026, PR #130

Live `main` reached `3e787da7de4efa1eaca7041c2a0bea9e80c8b984` after
the independently merged UI PR #131. PR #130 remains open; retain all UI work.
At review start, PR #130 head `47c869cbb635497674d745310ab599a23806a04f`
had three green GitHub workflows. Recheck CI on the new head.

PR #130 already addressed the literal YOUR-* template error. Further
hardening uses a shared, zero-network URL guard in preflight **and** live smoke
before credential creation, and redacts verifier rejection messages and
shadow assertion excerpts in the operator report. Cloud existence, model
deployments and trial credits are still **not verified**.

The operator's obsolete pre-rebrand Python directory on macOS has not been
inspected via the GitHub connector. Inspect tracked, untracked, ignored,
symlink and nested-repository data locally before moving it to a safe
out-of-repository backup. Preserve the branding regression test.

**Historical stop boundary superseded:** the operator successfully ran
live inference 18 October; future smoke execution is merge-only CI with
standing authorization. No operator PC execution or per-run approval.
No automatic retries, Azure resource creation or unapproved merge.

## 18 October operator logs and connected Foundry discovery

Operator preserved the ignored 192 KiB legacy Python bytecode cache tree
outside the repository; the obsolete pre-rebrand package tree no longer blocks local tests.
At the previous reviewed SHA, macOS passed **301 Python tests**, **29
frontend tests**, and Foundry DRY_RUN plus the offline preflight with a
real project URL. Local D2 --check validated the source diagrams but
reported a difference in generated `deployment.svg`, although Linux
CI passed. Collect `git diff` of the SVG after local regeneration before
changing renderer logic or committing generated artwork.

Connected read-only Foundry account access confirmed project
`matchpulse-ai`, deployment names `matchpulse-gpt5-mini` and
`matchpulse-gpt4o` (not `pitchvolt-*`), both Succeeded/20,000 TPM.
The existing resource identities remain unchanged. The linked Foundry
project has **no persistent agents**; creating one would not reproduce
the ephemeral SDK role/tool/verifier pipeline. This assistant's
container has no Azure CLI sign-in or available credentials, and no
billable model request was run through the connector.

The technical manager authorized relaxing the isolated test token policy.
PR #130 now uses the verified deployments; smoke-only budgets become 6144
Analyst / 1024 Storyteller output tokens and 30 seconds per role, with
a 70-second local preview total timeout. Production defaults stay at 256
and Foundry remains disabled there. Zero HTTP and role-level retries remain
for reproducible failure diagnosis. The engineer must not merge without
approval. The next authorized live test runs in GitHub Actions after
a PR merge, using OIDC. One-time IAM verification for the CI principal
may still be necessary; no PC involvement.

## 19 October 2026 — verified current state and NEXT PRIMARY WORKSTREAM

This section supersedes the older dated PR and priority snapshots above.
PR **#133 merged** on `main` at
`37bb23b286ce604c3889618ae1a25ee6dc6b8ecc`; frontend, Python and
architecture CI passed, while Azure deployment was still running at the
first post-merge check. PR #130 merged into `main` at `eb6f4299ebd4aa9c2679fc998bd6f74df62e4a80`; preserve the documented merge-only Foundry smoke-workflow authorization.
Always recheck actual GitHub status and the deployed SHA.

**Next major data/architecture milestone: GitHub Issue #134**
[Licensed synchronized football player/ball tracking](https://github.com/niktolis/pitchvolt-ai/issues/134)
(subtask of broad action-ROI Issue #129). The app cannot reach the approved
realistic 11v11/action-ROI depiction from synthetic MatchEvent actor locations
alone. PR #133's ball graphic is an **event-contact marker**, not observed
ball tracking or evidence of contested possession. First perform an
**offline source and legal feasibility PR** for Metrica Sports' synchronized
event+tracking samples: explicit redistribution permissions, actual player
and ball channels, event/sample synchronization, per-match identifiers,
sampling rate, null coverage, source SHA-256 pins and attribution. Do not
host, embed or publish original tracking data until the rights are
verified; do not mix historical game tracking with synthetic Harbor/Ridge
replay. Retain the separately verified StatsBomb 360 event-frame ingestion
as a distinct source adapter. Then design a versioned provider-neutral
spatiotemporal player/ball contract, tests, controlled historical mode
and ROI renderer. Ask for manager approval at each PR boundary. No new Azure resources or ad-hoc paid inference are authorized. The existing Foundry merge-only smoke workflow has standing approval; preserve its documented OIDC and budget safeguards.

**Parallel unblocked visual task currently in progress:** branch
`feat/ui-actor-visibility-preview-135` improves the existing single
source-positioned 3D player avatar, player surname/team-crest badge
legibility and side-aware label placement at pitch edges. This is a
presentation-only change: no new observed player, real kit logos, ball
trajectory or claim about actual athletic body pose. Validate CI,
review before merge, and manually compare exact deployed SHA against
the authoritative approved 1672 × 941 preview and latest uploaded image
`image(20261018-213428).png`.

Prioritize Issue #134 after this unblocked avatar-visibility PR. Do not
start another speculative CSS-only redesign or relabel PR #133 as ball
tracking. Maintain under-pitch replay controls and keep approved
three-card broadcast look and feel. Preserve DRY/provenance rules.

## 19 October 2026 — merged #135, Issue #134 offline feasibility delivery

Latest verified `main`: `7e6cdb3b83f5e856ea2589d4d3855b118668f0b0`
(PR #135 merged). Previous "actor avatar currently in progress" text
is historical: the improved source-actor avatar and badge are merged.
There are no open PRs at the start of this Issue #134 workstream.
The approved Application Preview plus later source-backed moving-ROI
camera and provenance rules remain authoritative.

**Primary next milestone / Issue #134: synchronized player/ball tracking.**
Do **NOT** assume Metrica source data is licensed for redistribution merely
because its GitHub repository is public. Pinned upstream
`metrica-sports/sample-data` commit
`e706dd506b360d69d9d123d5b8026e7294b13996`, games 1–2 CSV
player and ball tracking, synchronized event data, expected 25 Hz.
No LICENSE file found; public-use acknowledgement is not a redistribution
permission. Game 3 is a distinct EPTS/FIFA metadata/tracking format.

Current isolated branch `feat/134-metrica-offline-feasibility` implements
a **read-only, SHA-256-pinned local game auditor** (Home/Away/Events;
per-frame timing, player/ball coverage, event joins, unknown values,
no arbitrary network access), original synthetic unit tests,
`docs/architecture/metrica-tracking-feasibility.md`, and ignore
rules for locally acquired data. CI must pass before review.
No actual upstream 30+ MB tracking files were loaded in the assistant
runtime, so production compatibility with original bytes remains
**unverified**. Never claim otherwise.

Follow-on task after approval: obtain verifiable written permission or
choose clearly licensed tracking data, perform authorized offline original
CSV audit, design provider-neutral tracking contract, then a separately
approved historical ROI replay with real player and ball observations.
Never join to the fictional Harbor/Ridge replay and never fabricate
a ball carrier/duel from inferred proximity. No public source-data
hosting, billable inference or Azure provisioning in this bundle.
Keep the existing **approved merge-only Foundry smoke** workflow intact.

### Metrica offline audit provenance hardening (19 October)

Before merge, the #136 review found SHA-256 supplied by the operator
and commit supplied by the operator were not cryptographically linked.
The auditor now embeds the six actual Git blob OIDs/byte counts from
the exact pinned Metrica upstream commit, and verifies local data
against SHA-256 AND Git object identities, without network calls.
Source event joins now require period+frame. No upstream bytes added to
Git; no hosting license inferred. All synthetic test fixtures are
explicitly marked not upstream-bound.

## 19 October 2026 — verified #136 merge / current parallel UI work

Post-review PR #136 is **merged** at
`37de0d762f7fdb1df37509c4a55ddcbd4dd45a5c`.
Do not replace its hardened `metrica_offline_audit.py`: it now checks
original Git blob OIDs against the pinned public upstream tree as well
as SHA-256 and enforces source frame/period joins. These changes
strengthen the **offline audit only**; no right to redistribute
original player/ball tracking or run a public historical replay
has been established. Issue #134 remains open, and Metrica data should
not be copied into production. Foundry PR #137 is also merged and
retains the explicitly approved merge-only smoke workflow.

The next non-blocked UI bundle is branch
`feat/ui-key-moment-source-3d-138`: replace flat 2D Key Moment location
diagram with a **real Three.js camera close-up** of the same source
recorded actor, ball-contact marker only when eligible, fixed field
infrastructure, kit color and validated fictional team/player badge.
It does not claim to be a game photo. SourceMomentPreview retains an
accessible 2D fallback and the second camera renders on demand rather
than running its own perpetual replay clock. Reuse all existing 3D
mesh and source validation logic; do not create a second coordinate
mapping or new players. Continue preserving the approved three-card
broadcast design and usable replay controls beneath the primary pitch.
Dedicated screenshot comparison against exact deployment SHA remains
outstanding. CI and explicit manager merge approval are required.

## 19 October 2026 — merged #138, #139; UI source-action analysis bundle

Latest verified main `946caf4c9006c3aa0160d099d17cbabac6dc2725` is
PR #138, cinematic 3D Key Moment; PR #139 source-neutral observed
tracking **schema** merged previously at
`3fa7d684a60e2e91274a71ee2d68e50d0b257f89`.
No tracking license/hosted true athlete or ball samples were introduced
by that contract. The #138 deployment was in progress at the latest
initial check. Preserve all source identity + license/rights gates
for Metrica and StatsBomb 360, and the approved Foundry merge-only
smoke process. No new billable inference is authorized here.

Branch `feat/ui-key-moment-action-details-140` makes the approved
Key Moment View Analysis CTA functional even before AI tactical
insights are published. Existing insight-click behavior is retained
when an insight exists. Otherwise the button opens a snapshot-only,
cursor-gated, source-recorded facts overlay with honest possession
and under-pressure/unknown ball statuses and a close control.
The right card does not grow and the approved cinematic appearance
remains at rest. Verify regression tests and CI before presenting it
for review, never merge without manager approval. After exact deployed
SHA #138/#140 screenshot, compare with the approved design again.

## 19 October 2026 — PR #141 merged, Key Moment fidelity work underway

Verified GitHub main `e28eac6f40963888ee3f9b593bd1c6e4f31c3ee5`
is merged PR #141, source-only Key Moment View Analysis CTA. PR #138
3D close-up and PR #139 observed tracking schema also merged previously,
but genuinely observed multiple athletes/ball from a licensed original
dataset remain outstanding (Issue #134). No inferred tracking is allowed.

Current isolated branch `feat/ui-key-moment-render-fidelity-142`:
medium-detail self-contained 3D Key Moment hero, cloth shading, lighting,
closer camera and instance-batched local grass scene. Only editorial
static pose changes follow event category; **source event coordinates,
real play/ball coordinates, possession and body tracking do not change**.
SVG fallback, fixed target broadcast layout and existing replay
transport are preserved. New Issue #142 records the longer-term
self-hosted verified CC0 realistic athlete GLB/LOD workflow, separate
from licensed match observation Issue #134. Third-party candidate GLBs
were researched but **not verified or loaded** and must not become a
brittle runtime CDN dependency. CC0 candidate research includes
https://www.innerscene.com/tools/library/3d-parts/soccer-player-standing-3d-person-team-sports-f55b1b4f
and kicking/running versions; verify binaries, checksums and optimization
before shipping.

Do not overstate EA FC-level realism from this procedural-only PR.
Run complete frontend/TypeScript/Vitest/Python/architecture checks,
request review, do not merge without manager approval. Await exact
production SHA and same-resolution screenshot for visual signoff.

## 19 October 2026 — approved #143 merged, Issue #142 licensed hero pipeline

PR #143 was **explicitly approved and merged** at
`808215a495f9e79af3ca8414c919d90640858334`. Before it,
independent Issue #134 offline tracking PR #144 merged at
`8553bc11e21697182c923c22de13daee69f6d7be`,
adding verified IDSSE Sportec source audit. Preserve the entire
rights/provenance gate and independent Foundry workflow decisions;
neither PR provides independent sampled match tracking or
authorization to invent athlete coordinates.

The next feature branch is
`feat/142-verified-hero-asset-pipeline`: 
**production-safe, opt-in, same-origin, SHA-verifiable soccer GLB import,
not yet a shipped third-party player mesh.** It adds a GLB binary
structure/triangle-size/URL/CC0/kit-material validator; build-enforced
public manifest file hashes; a local import CLI requiring original
SHA-256 and source provenance; and a R3F loader which uses a
fingerprinted self-hosted model if truly included, otherwise
keeps #143's medium-detail physically shaded procedural avatar.
The empty default manifest means **no remote model download in production**
and no change in player position semantics. Do not claim this alone
has reached EA FC visuals.

Approved Innerscene CC0 catalog entry for standing/running/kicking:
https://www.innerscene.com/tools/library/3d-parts/soccer-player-standing-3d-person-team-sports-f55b1b4f
and https://www.innerscene.com/tools/library/terms .
Original GLBs are advertised as 17.5 MB / 112k triangles;
**not inspected or downloaded in this runtime**. Therefore no
source SHA, optimized binary, materials, actual performance or visual
integration is claimed. Follow `docs/architecture/hero-assets.md`
to acquire under CC0, optimize to <=4 MiB and <=90k triangles,
inspect kit material name, and prepare a separate verified binary PR.
Never hotlink a model/CDN at runtime or ship unrelated source assets.
This is a **distinct task from Issue #134** tracked player/ball data.
User supplied approved target and actual screenshot; exact-SHA
real deployed screenshot remains mandatory to accept fidelity.

Run CI fully, mark Ready for Review, request manager approval;
never merge this follow-up without explicit approval.

## Immediate blocking operational state — GitHub-hosted Actions failure (19 October 2026)

Independent **Issue #149** records a repository-wide hosted-runner
failure, https://github.com/niktolis/pitchvolt-ai/issues/149.
PR #143 was explicitly merged to main at
`808215a495f9e79af3ca8414c919d90640858334`, but the subsequent
`main` deployment, merge-only Foundry smoke and ALL usual CI jobs
failed before assigning any runner or executing checkout. PR #148 and
other independent feature branches show identical instant failure.
Job API: `steps=[]`, `runner_name=""`, 404 `BlobNotFound` logs.
A targeted frontend rerun failed identically. This is a **CI
infrastructure/account-level blocker**, not test evidence.

Suspect private-repo Actions free-minute exhaustion, spending limit,
billing hold or runner-entitlement issue, but **billing state not
verified**. Repository owner must inspect GitHub account Actions billing,
quota, spending limit and payment failures, or contact GitHub Support.
Do NOT spend money, increase spending limit, enable a self-hosted
runner, change repository privacy or relax required checks without
explicit manager approval. PR #148 MUST REMAIN DRAFT until actual
frontend/Python/architecture workflows execute and pass. Latest #143
production appearance is unverified because deployment failed.
Manual local test commands after entitlement repair are documented
in `docs/architecture/hero-assets.md`.

## CI and deployment recovered — update superseding the earlier blocker (19 Oct 2026)

The earlier runner-provisioning blocker **Issue #149 is closed**:
the repository owner deliberately made the repository **public** and
applied GNU AGPL-3.0. All checks plus the Azure deployment now
succeed on `main` at
`65f026083eb92db2543f3253776824a2a0513a52`.
GitHub run IDs: Frontend `39249830666`, Python `39249830606`,
Architecture `39249830657`, Azure deployment `39249830616`.
This establishes successful deployment workflow execution but
**does not** establish visual screenshot acceptance of PR #143.

PR #148 (`feat/142-verified-hero-asset-pipeline`) resumed
full checks after repo visibility changed. Four genuine Biome
errors were corrected and a Node-only model verifier was removed
from Vitest discovery (it runs instead under `npm run assets:check`).
The frontend, Python, architecture and production build on
`f095bc9955089aa8cdc09663ec502f715b2752ad` all passed.
This follow-up documentation commit itself requires its own final
CI verification before the PR is ready to review. No realistic
GLB was imported: the default manifest remains empty, and the
post-#143 procedural avatar is the current shipped visual.
The first actual source-verified model import/optimization remains
next once PR #148 is approved and merged; see Issue #142.
Never merge without explicit technical-manager approval.

Concurrently merged legal work on `main` is PR #145:
standard AGPL-3.0 license, repo public; preserve the user's
licensing decisions and do not accidentally reintroduce proprietary
notice language or remove license files.

## 19 October 2026 — PR #148 merged and real CC0 player asset branch

PR #148 was merged at
`49561456f6df2ba666a8cd3964fe3f9024ef77e9`.
The next branch `feat/142-cc0-real-footballer` has completed a
**real official CC0 model import**, unlike the prior empty-manifest
stage. Original Innerscene GLB SHA
`773cfa73bbcf659d7044934aaeacf1c3c9a49ae2955a51f56de7ad61ad1b6ffb`
at 18,349,744 bytes, optimized local-integration GLB SHA
`5bb8a63f2824d84c4f8a346ca11d6af0eefd1854050cfa3dde4fb12a134c6591`
at **2,583,972 bytes**, **70,839 triangles**. File is checked in
at `web/public/assets/hero/neutral-5bb8a63f2824d84c.glb`.
Material `Micah | top` retained for team-color recolor. CC0 terms
from https://www.innerscene.com/tools/library/terms .
One-shot GitHub Action audit/import completed at
https://github.com/niktolis/pitchvolt-ai/actions/runs/39255686666 ,
then the privilege-bearing workflow was **deleted** from branch.
Source and build SHA bounds were enforced using PR #148 tools,
no external model network dependency remains.

Current source's *standing* figure is non-animated illustration
for all available action categories. It is not live observed body
pose, a reconstructed shot, opponent/player tracking, 22-player
formation or live ball position. Next real gameplay motion work
remains gated by independent data Issue #134. Multi-pose realism
(running/kicking) could be a subsequent optimized asset bundle
only after actual bytes are checked; do not guess source data or
claimed poses.

Run green frontend/Python/architecture CI, present one
manager-reviewable PR and **do not merge without approval**.
After manager deploy, request a current screenshot to compare with
authoritative approved pitch preview. Verify body/ground orientation,
team kit material isolation, badge position and GPU performance;
do not claim visual match merely from compiled GLB.

## 19 October 2026 — corrected duplicate ball and action-specific GLBs

Previous PR #151 is merged and deployed, but the manager's actual
screenshot revealed **two visible footballs** at the Key Moment actor,
a static mannequin-like body and inconsistent character styling.
Implementing branch `feat/ui-cc0-action-pose-prop-safety-153`:
three same-Micah Innerscene CC0 standing/running/kicking variants,
all independently original-SHA-pinned, optimized under 4 MiB and
90k tris, and supplied as first-party fingerprinted GLBs. **All**
decorative `Soccer ball |` / `Soccer jersey number` model props
are excluded at GLB scene-graph build time using
`web/scripts/strip-hero-props.mjs`; production CI also requires no
reachable props and runtime filter remains. Shared rejection policy
is `web/src/assets/unobservedHeroProps.json` (DRY).
Posture selection maps carries/pressure to running, pass/shot/goal
to kicking; turnover/other to standing. Closer 3D Key Moment
camera, no altered source location, no invented ball/athlete motion.

See `docs/architecture/hero-assets.md` for all verified original
and optimized hashes, node-removal semantics, files and models.
The private, temporary import workflows were removed after source
verification and commit. Run all three complete CI checks, leave
a reviewable PR unmerged until technical-manager approval. Screenshot
at exact deployed SHA remains essential to validate no double ball,
character appearance and action-readability. Issue #134 tracks
separately licensed genuine multi-player tracking. Do not touch
its ongoing work or claim actual skeletal movement from these
static action-category illustrations.

## Additional user-requested UI change in PR #155: immediate pitch time bar

The current action-specific CC0 model/provenance PR also contains the
user-requested **time scrubber immediately under the tactical pitch**.
`Pitch` accepts the one existing `seekControls` JSX from `App`,
placing Play/Pause, −2s, single canonical 100ms-step range slider and
+2s between the pitch and ball facts. The events/timeline and advanced
configuration remain below in `pitch-replay-deck`. No duplicated
clock/seek state, SSE logic change or new tracking inference.
Responsive dark-lime styling and source order regression tests
were added. Verify seek/drag, timeline sync, keyboard access,
and mobile wrap after exact deploy SHA. **Do not merge PR #155
without manager approval and full final-head checks.**


## PR #154 integration after merged #155

The original historical replay branch predates main PR #155. Resolved its conflicts preserving same-Micah sanitized GLBs and the canonical synthetic time bar, consolidating the historical transport directly beneath the pitch. The derived-source `public_replay_enabled:false` field requires explicit release interpretation; CC BY 4.0 does grant attributed re-use but is separate from internal product publication control. No public release is authorized by this merge conflict-resolution commit alone.
