# PitchVolt AI — dedicated UI / broadcast experience handoff

**Handoff date:** 18 October 2026 (Europe/Berlin). **Hackathon deadline:** 27 October 2026.  
**Repository:** https://github.com/niktolis/pitchvolt-ai  
**Project:** https://github.com/users/niktolis/projects/6  
**Production:** https://pitchvolt.app  
**Primary overall project handoff:** [handoff-next-chat.md](handoff-next-chat.md)

> **Start the next UI chat here.** First inspect actual GitHub `main`, open PRs/issues
> and deployment status; the SHA and PR state below are a dated snapshot, not a
> substitute for live checks. This is a **UI implementation handoff**, not a
> license to automatically merge changes or fabricate football observations.

## 1. Exact approved screen — NON-NEGOTIABLE design authority

The **second screenshot** in the prior PitchVolt UI conversation, the **Application
Preview** from the approved PitchVolt branding kit (uploaded as
`Neon Football Analytics Dashboard(1).png`), is the *sole visual target*.
The user explicitly rejected alternative concept images or independent
redesigns. Preserve the brand-kit **PitchVolt AI** lightning-P logo,
pitch-black / stadium-green backgrounds, Volt-green `#B6E64B`,
`#060F0B`, `#132318`, white `#F8FAFC` and neutral `#9CA3AF`.

Visual specification from that target:

- **Stadium atmosphere:** full-screen football-stadium background, glowing
  floodlights and dark pitch ambience, not a blank flat green page.
- **Top shell:** original P logo/wordmark, Live/Matches/Analysis/Teams nav
  and restrained utility icons; centered fixture/scoreboard with team
  identities, badges, match clock and a status indicator; the tab strip
  immediately beneath.
- **Hero layout:** three columns — compact **AI Insights** card on left,
  largest **tactical pitch** in center, **Key Moment** card on right;
  reproduce relative widths, heights, whitespace, pitch scaling, font
  hierarchy, borders and lime accents of the screenshot.
- **Pitch:** near-full-bleed broadcast grass, texture, depth, camera
  perspective, stadium lighting, crisp field markings and source-backed
  highlighting. The play/pause overlay shown in the reference must have
  real playback behavior.
- **Right panel:** dramatic high-quality Key Moment area and concise
  event text / **View Analysis** action. Any generated visual must reflect
  actual available source facts; do not invent an action photo, player,
  ball location or real match.
- **Replay controls** are REQUIRED and must remain **visible directly
  beneath the pitch**, together with the compact source event timeline.
  Preserve play/pause, ±2-second seek, speed, scenario, restart, scrubbing
  and casual/analyst/club modes. Do not move controls above the
  three-column hero or hide them in a collapsed drawer.
- **Evidence detail** is below the primary hero and must remain accessible,
  but should not distort the target's primary composition.

**Important distinction:** The reference image contains illustrative real
club crests, real-looking scores, multiple illustrated players and match
photography. These are **design cues, NOT authorized football data**. Recreate
the *composition and aesthetic* with validated fictional fixture metadata
and available source-backed observations. Do not assert the depicted
Manchester City–Arsenal score, invent source player positions, scrape or
use unlicensed crests/photographs, or insert placeholder formations.

**Reference durability:** The *exact* approved screenshot is an attachment
to the previous project UI chat; its presence as an image in GitHub is **not
verified**. In a fresh chat, request the user to reattach **the approved
target screenshot** if it is not visible, before declaring visual
acceptance. This textual layout contract is durable but cannot replace
pixel-level reference inspection. The user routinely uploads a new
**actual production screenshot** after deployment; compare the two,
never an assistant-invented substitute.

## 2. Confirmed GitHub baseline and PR boundaries

As checked on **18 October 2026**, `main` points to merge commit
`bc18c9a7e7939181bd3cb08067556fc532f793d4`, **PR #117 merged**:
https://github.com/niktolis/pitchvolt-ai/pull/117

**What #117 actually delivered (source inspected on main):**

- `web/src/domain/replayClock.ts`:
  `recentInsightsAtCursor(messages, cursorMs, limit=3)` shows only
  **published tactical insights** with timestamps no later than the
  canonical replay cursor; newest first; no synthetic filler insights.
- `web/src/App.tsx`: interactive compact AI insight feed (up to three
  rows), clicking a row seeks to its source event time via `inspect`,
  which requests evidence. Latest verified metrics remain available
  in `<details>`.
- `sustained_possession` uses **sequence duration and passes** rather
  than press-to-shot `transition_duration_ms`/`attacking_actions`.
- `BroadcastPitchScene.tsx`: the only drawn 3D player is the recorded
  event actor, annotated by its **recorded event clock** and identifier;
  not presented as continuous real-time player tracking.
- PR #117 includes replay/possession regression coverage and no
  public wire-schema change. Do not infer a deployment is visually
  accepted just because the PR merged or CI passed.

**Separate in-progress workstream:** PR **#118** was **open** at the
18 October inspection:
https://github.com/niktolis/pitchvolt-ai/pull/118

It addresses issues **#59/#60**: validated **fictional** team/roster
metadata, source-derived scoreboard and explicit substitutions; it also
touches the **general handoff**. **Do not race that PR, overwrite its
data models, merge it automatically, or edit the general handoff
concurrently.** Recheck its current state before UI work, coordinate
changes and consume its validated client contract *after approved merge*.
No assumed 0–0 score for excerpts without authoritative initial state.
No made-up goal/substitution records.

**#116 unified replay source contract** is present on `main`
(`src/pitchvolt/replay_dataset.py`), but its delivery is **not** full
historical-data browser integration. Read
[replay-data architecture](architecture/replay-data.md) before touching
source provenance or time semantics.

**Unresolved UI-related issues:** #18 (broadcast polish/team colors),
#61 (source-validated pitch labels), #63/#58 (cursor and replay
synchronization), plus #59/#60 as dependencies. Check latest issue state,
linked PRs and GitHub Project views first; do not close issues from
partial work.

## 3. Current implementation: actual source paths

- `web/src/App.tsx`: page composition, scoreboard placeholders, verified
  multi-insight feed, replay cursor and controls, evidence/narrative
  interactions, Key Moment panel and audience modes.
- `web/src/components/Pitch.tsx`: pitch container, centered accessible
  play/pause overlay, SVG fallback and source actor gating.
- `web/src/components/BroadcastPitchScene.tsx`: Three.js/R3F 3D pitch,
  perspective camera, deterministic turf texture, 3D player at recorded
  event coordinate, event arrow only with an original destination.
- `web/src/components/pitch-geometry.ts`: shared 105 × 68 m field,
  source coordinate validation, camera frustum fit, world conversion
  and destination-anchored arrow geometry.
- `web/src/components/SourceMomentPreview.tsx`: **source event mini-pitch**
  in Key Moment, not an invented photo or guessed ball/player scene.
- `web/src/components/EventTimeline.tsx`: event/time selection rail,
  positioned below the central pitch.
- `web/src/domain/replayClock.ts`: single authoritative replay cursor,
  visibility filtering, seek bounds and source-published insight feed.
- `web/src/domain/presentation.ts`: source-derived display labels and
  audience copy; never put football rules in CSS or component markup.
- `web/src/styles.css`: accumulated UI styling and responsive overrides;
  check the **final cascade** before adding further ad hoc overrides.
- `web/public/pitchvolt-mark.svg`, `docs/assets/`,
  `README.md`: committed logo/brand assets and palette.
- `docs/architecture/frontend.md`,
  `docs/architecture/pitch-rendering.md`,
  `docs/visual-acceptance.md`: existing behavior and design constraints.

**Real capabilities:** React 19 / Vite / TypeScript / Three.js / React Three
Fiber / Drei, synthetic `/timeline` snapshot with replay clock,
visible play/scrub/speed controls, evidence and local controlled
narratives, source actor annotation, SVG fallback. Score on the current
main UI can be **unavailable**; current shield initials are not approved
original crest artwork. Fixture names currently derive from observed
event team IDs until validated #118 metadata is integrated.

## 4. Data/temporal integrity — MUST preserve

1. The browser must render **strictly source-backed player positions**:
   no made-up 22-player XI, no synthetic tactical formation, no inferred
   goalkeepers, no smoothed paths, no arbitrary ball marker, no interpolated
   position between recorded timestamps, no off-field clamping.
   A player shown after its original timestamp is explicitly an
   **observation from that earlier event**, not tracked at `cursorMs`.
2. Synthetic scenarios are fictional but are **valid source events** for
   this app. Historical StatsBomb Open Data is separate real source
   material; preserve original file digest, match ID, timestamp,
   source UUID and type coverage. Do not relabel or silently convert it
   into synthetic `MatchEvent`.
3. StatsBomb **360 freeze frames are sparse and anonymous**, not a
   22-player continuous feed. The previous source audit found **8**
   fully 11+11 populated frames out of **3,914** inspected for
   historical match 3764440; do not synthesize absent player slots.
4. A trajectory is allowed **only** with a validated recorded source
   destination, and must terminate exactly at that endpoint. The source
   event schema does not supply an independent continuous ball position.
5. The same integer-millisecond cursor governs pitch observation,
   timeline, published insights, evidence and local narrative
   visibility. On rewind, hide future events/insights/evidence/narratives;
   cancel or guard stale async responses when moving between
   scenarios/insights/modes.
6. The published multi-insight list is not a prompt for LLM-written
   extra facts. No unverified possession %, pressure, goal/chance or
   player attribution. Controlled free-form AI output is **not** enabled
   on the public app.

## 5. Known UI fidelity gaps / review priorities

The last user-supplied UI comparison showed a substantial gap against
the approved cinematic preview. Subsequent PRs improved the scene,
header, control placement, source event labeling and insight feed, but
**no post-#117 screenshot has been reviewed in this handoff**.
Treat these as **items to verify**, not assertions about the latest
production rendering.

| Priority | Design/behavior target | Grounded current state and next check |
| --- | --- | --- |
| P0 | Match target's overall stadium atmosphere and panel proportions | Check current live full-page screenshot at same viewport; avoid unrelated redesign or random CSS changes |
| P0 | Main pitch visually fills its column, credible perspective/grass/shadow and source actor overlays | Inspect 3D camera fit and actual canvas aspect; test source coordinate projections and arrows, retain SVG fallback |
| P0 | Replay remains visible directly beneath pitch | Validate scrub, pause/restart, 1x/5x/25x, ±2s, event timeline and keyboard-accessible controls |
| P0 | Accurate current replay cursor across all panels | Test rewind/future-leakage, evidence selection, actor recorded time vs cursor time, stale narrative/async update |
| P1 | Three compact, credible AI insight rows (when facts exist) | Confirm #117 result in deployed UI; the `extended_match` publishes several bounded insights but shorter excerpts may publish only one |
| P1 | Broadcast scoreboard/crests/side colors and player identity | Integrate only approved validated fictional metadata after #118, never hardcode real fixture names or claim a known score for excerpts |
| P1 | Key Moment panel's image-style visual treatment | Source-only depiction, or permissioned media if explicitly approved; do not pretend a synthetic clip/photo is authentic |
| P1 | Responsive layout, spacing, font and neon accent matching approved preview | Capture reference/actual at identical desktop viewport and also review tablet/mobile |
| P2 | Simplify accumulated CSS, improve mobile performance and contrast | Avoid code churn until measured layout diffs; preserve R3F performance and no WebGL fallback regressions |

**Past rendering regressions to avoid:** the first WebGL PR produced a
smaller, flat-looking pitch; camera-only adjustments failed to match
the target and generated broken arrow visuals. A later source-backed
scene fitted the camera and anchored arrows. **Do not assume another
camera/CSS tweak is an acceptable substitute for comparing real screenshots.**

## 6. Visual verification process

- **Do not revive the automatic post-deployment screenshot pipeline.**
  It was removed because images were captured too early and were
  misleading. Keep this decision unless the user explicitly revisits it.
- Azure CI checks application health and waits until public
  `https://pitchvolt.app` HTML contains the **exact deployed Git SHA**
  in the `pitchvolt-build` meta tag, using cache-busting probes.
  This confirms release identity, **not** visual correctness.
- Only after successful exact-revision readiness, perform a **manual
  browser comparison**. The user can supply current-production desktop
  screenshots from `pitchvolt.app`; compare with the approved image,
  identify measurable differences, then fix via a focused PR.
- `docs/visual-acceptance.md` documents optional local Playwright
  (`scripts/capture-live-visual.py`), not an always-on CI screenshot job.
  Do not claim website visuals have been inspected if only a build or
  HTTP page probe was checked.

**Acceptance criteria per UI PR:** source-based correctness, layout parity
with the approved preview, functioning replay, passing Python/TS tests,
responsive accessibility, no fabricated data, and user review on the
verified deployed revision. Report what is implemented separately from
what is visually accepted.

## 7. UI development procedure / constraints

1. Begin each session by reading this UI handoff **and**
   [general handoff](handoff-next-chat.md), then query live `main`,
   issues, open PRs and CI. PR #118 or later may have changed the
   validated presentation contract: re-check before editing UI.
2. Branch from fresh `main`; **one bundled PR at a time**. Scope UI
   changes clearly, explain the actual intended rendering/business
   behavior and keep docs/diagrams/source schemas DRY.
3. Maintain React-generated TS contracts from OpenAPI and D2 source/SVG
   consistency. Do not create a duplicate event-time or provider model
   in frontend code. Avoid concurrent modifications to PR #118's files.
4. CI checks (fish or bash):
   `uv sync --frozen --extra dev`;
   `uv run --frozen bash scripts/check.sh`;
   `npm ci --prefix web`;
   `uv run --frozen bash scripts/check-web.sh`;
   `bash scripts/render-architecture.sh --check`.
   Node comes from `.node-version` (currently 26.10.0).
5. **Do not auto-merge** after green checks: present technical-manager
   report and await explicit user approval. Include changed source
   locations, actual football behavior, test results, risks and next
   deliverable. Once approved/merged, update this UI handoff with new
   baseline SHA and the accepted/deferred visual differences.
6. No new Azure resources, billable Foundry deployments or model
   inference, licensing assumptions, GitHub corporate org app
   permissions, or financial consumption without explicit user approval.
   Existing Azure resource names are intentionally retained; see the deployment workflow.

## 8. Starting point for the next UI chat

**First:** verify PR #117 is in current main; check whether **#118**
has merged or remains open; identify current live deployment commit and
request the latest actual screenshot only when needed.

**Next candidate scoped UI work, after checking #118:** faithfully align
the AI Insights / Pitch / Key Moment *three-column composition* and
replay controls with the approved design, and integrate validated
fixture branding when its source contracts are ready. Inspect
`App.tsx`, `BroadcastPitchScene.tsx`, `SourceMomentPreview.tsx`,
`pitch-geometry.ts`, `replayClock.ts` and final `styles.css`
cascade before deciding the PR. Never fill the field with imaginary
teammates to mimic the mockup.

**Handoff update requirement:** every substantial UI bundle must update
this document (current SHA, PRs, acceptance status, unresolved defects)
before the next context switch. Keep general cross-workstream
`handoff-next-chat.md` in sync after its owner has merged competing
work and avoid edits to it while #118 is open.

## 9. Copy/paste prompt for the next ChatGPT UI chat

> Continue the **PitchVolt AI broadcast UI** implementation for the Microsoft
> hackathon in repository **https://github.com/niktolis/pitchvolt-ai**.
> Before making any code changes, read **docs/handoff-ui-next-chat.md**
> (the UI handoff) and **docs/handoff-next-chat.md** (overall project state)
> from current `main`. Confirm PR **#117** merged; inspect PR **#118**
> and do not conflict with its pending fixture/score/substitution work.
> 
> The approved **PitchVolt Application Preview** from our brand kit is
> the **exact visual specification**, not inspiration. Do not produce an
> alternative design. If the target screenshot isn't accessible in this
> chat, ask me to attach it; I will upload the latest `pitchvolt.app`
> screenshot after deployments. The principal goal is pixel-faithful
> stadium background, header/scoreboard, three-column **AI Insights /
> 3D Pitch / Key Moment**, player-source overlays, responsive styling.
> **Replay controls and event timeline must remain visible below the
> pitch.** Investigate the rendered result, not just CI status.
>
> **Strictly source-backed player coordinates only.** No illustrative
> 11v11 formations, inferred player tracking, guessed ball or player
> positions, invented results/insights, or real club media without rights.
> StatsBomb 360 is sparse historical freeze-frame data, not continuous
> 22-player tracking. Preserve original source IDs and the canonical
> replay cursor; hide future events/evidence/narratives when seeking
> backwards. Only display verified synthetic team identities, badges,
> score and substitutions when their API contracts are merged.
>
> Work on **one focused PR at a time**, branch from fresh `main`,
> explain the UI architecture and football logic and update diagrams,
> tests, and the UI handoff. Run Python, frontend, OpenAPI/TS and
> architecture validation. **Do not merge without my explicit technical
> manager approval**, even when all CI is green. Do not provision or
> charge Azure/Foundry resources. Give me a concise technical-management
> report per PR, including risks and remaining target-vs-actual gaps.

## 10. Next isolated UI PR — source-event timeline accessibility (18 October 2026)

Branch: `fix/ui-timeline-source-navigation-120` (created from main `681041c419c258215e14f1512ef5e76c9200e279`).
Only `web/src/components/EventTimeline.tsx` and this UI handoff are modified; no scoreboard, backend, shared stylesheet, pitch rendering, or Azure changes. The event rail announces its purpose to assistive technology, exposes the selected event/insight through `aria-pressed`, and names each source-clock navigation action rather than making the constantly growing rail a live region. It does not add events, alter selection/cursor logic, or invent tracking.

Review status: implementation proposed for manager review, not merged. Check its CI after PR creation and confirm visual parity with the approved image only after a verified production deployment; no production screenshot is claimed. PR #118 remains a separate draft changing App/Pitch/CSS and must not be merged by this UI workstream.

## 11. Post-merge replay evidence integrity — proposed PR #121 (18 Oct 2026)

At the current baseline, PR #118 (fixture metadata) and PR #120 (accessible source timeline) are both merged; main `78983af32d11176134d4a9b2bc1851d662b2882c`. Branch `fix/ui-evidence-cursor-integrity-121` changes only App replay navigation and this handoff. It guards late evidence fetch responses by request epoch, cursor and source insight ID. Navigating to another source event clears evidence immediately; scenario changes invalidate prior requests. The Key Moment "View Analysis" selects the most recent published insight visible to the canonical cursor, not the earliest message.

No invented football facts or new API. Full test/CI evidence must be checked before review; the PR is not visual acceptance. The approved preview remains the sole reference and a manually captured production screenshot at confirmed deployed SHA remains outstanding. Never merge without explicit approval.

## 12. Next PR: cursor-synchronized event selection (18 Oct 2026)

PR #121 merged on main at `b32bea425b55bef038a3a47c124802e7527e40e5`. Candidate branch `fix/ui-cursor-selection-sync-122`: source event inspection pauses the replay, while resuming or manual seek discards stale manually selected actor IDs. The pure `selectedAtCursor` helper additionally ensures a selected event only overrides the canonical latest event at its exact source clock and while paused. Regression tests cover stale selection after playback and rewind. No synthetic tracking, WebGL changes, new assets or paid models. Require green CI and explicit merge approval; this is not visual acceptance.

## 13. Evidence-to-pitch navigation (18 Oct 2026)

PR #123 merged at `c0bc2fc3eb25a412da90417f2396ab0d8aaa01d8`. Next focused UI branch `fix/ui-evidence-event-seek`: evidence event buttons route to the existing `inspect(message)` callback instead of only changing `selectedId`. This ensures the canonical cursor seeks to the exact recorded evidence event timestamp and playback pauses, aligning the evidence click with source event selection semantics introduced by #123. The selection uses existing visible canonical MatchEvent records; there is no inferred position, additional timeline model, backend change or Azure resource. Run required CI; no merge without explicit approval. This is not screenshot-level visual acceptance.

## 14. Pitch-stage vertical alignment (18 Oct 2026)

PR #124 merged as `1f92f4073c53116282aae1c38de495b2ef268f6d`. Branch `fix/ui-pitch-panel-top-alignment` changes `.pitch-panel` flex justification from center to flex-start. This avoids top padding introduced by vertical centering when the neighboring broadcast grid cards are taller. The source event timeline and functional replay transport remain immediately beneath the pitch. No changes to player locations, camera projections, score, evidence, Azure resources, or model inference. CI and manually verified exact-SHA screenshot comparison remain necessary; do not declare pixel-level acceptance or merge without explicit approval.

## 15. Source-validated 3D actor heading (18 October 2026)

PR #126 merged at `1bcd42e57b921434ba2b23eb7e258aa3f4ddf7f9`. The parallel editorial PR #125 is open and changes App/Timeline/CSS; do not overlap. Branch `fix/ui-source-validated-actor-heading` fixes the 3D actor body heading to depend only on valid in-field source destinations; missing, nonfinite or outside-field destinations result in neutral pose. A previously invalid destination could affect actor orientation despite its directional arrow being correctly suppressed. Shared pitch geometry and its regression tests are updated; no source coordinate, pitch camera, visuals, event schema, synthetic tracking or Azure changes. Source-backed correctness improvement only, not pixel-level visual acceptance. All CI required, explicit approval before merge.
