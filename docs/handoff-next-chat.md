# Foundry merge automation checkpoint — 19 October 2026

**CURRENT POLICY OVERRIDES HISTORICAL OPERATOR STOP NOTES BELOW.**
PR #130 remains open. The technical manager has standing-authorized one
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
