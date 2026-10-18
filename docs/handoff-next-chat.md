# PitchVolt AI — authoritative project and next-chat handover

**Updated:** 18 October 2026, during issue #58 event-activity implementation (PR #125, based on post-#123 main).
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
3. **No new Azure charges or Foundry model calls** without explicit approval.
   Public app runs deterministic/local controlled narratives; paid
   Microsoft Foundry inference is disabled. Budget alerts are not a
   hard spending cap; ask before any live model smoke.
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

## Next prioritized implementation after #118

1. **Editorial action ticker #58 (PR #125 under review)** and remaining temporal
   edge cases #63 (P0). A compact `recorded-action-feed` below the pitch
   selects the three latest **actual match_event** records at or before the
   authoritative replay cursor. It never fills gaps with fictional play,
   creates a tactical insight, or derives a ball/player trajectory. The
   existing `recentInsightsAtCursor` three-insight feed is separate.
   Confirm PR #124 evidence navigation and UI screenshot before merging
   overlapping work. After #125, test stream completion, audience switches
   and long replay seeking end-to-end.
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
   publication fell back on `fact_order` validation. Require separate
   approval, token/latency limit and measured costs for new billable smoke.
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
Use only source-backed positions. No paid Foundry inference or new
Azure charges without my separate approval. Update the general
handover with every merged delivery, run complete tests, and wait
for my merge approval."
