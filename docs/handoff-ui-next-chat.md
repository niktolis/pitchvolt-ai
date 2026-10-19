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

## 16. APPROVED NEXT PITCH TARGET — action ROI, camera, badges (18 October 2026)

Owner feedback after merged PR #127 (main de4625e01bae9f7e830d1db7be08b19eee687553):

- **Larger central pitch**: physically larger primary 3D viewport; maintain the three-column broadcast composition and keep the timeline and fully usable replay transport beneath it.
- **Camera tracks the action**: frame a zoomed region of interest around a real source-recorded event; visibly pan between source actions as an editorial camera, rather than keeping all 105 x 68 metres onscreen.
- **Participants**: prefer **selective attackers plus defenders who actually contribute to the action**, within that ROI. Showing all 22 is only an alternative if valid per-player positions exist. NEVER place illustrative formations, fictional off-ball defenders or a pretend ball. The current schema has one source actor per event; StatsBomb 360 freeze-frame ingest and validation would enable sparse participant snapshots, not continuous tracking.
- **Player tags**: source-authored player **surname plus team crest/logo** (fictional validated emblem where no licensed image exists); label must sit beside/above the player and not obscure the body, with edge/overlap handling.
- **Playback glyph**: central in-pitch play/pause is **completely invisible during playback**, and **very transparent when paused**. The real controls below the pitch remain visible and functional.

Priority: fulfill these before further minor UI polish. This feedback is an additional binding acceptance requirement alongside the single approved Application Preview screenshot. Do not confuse visual goals with currently available tracking data.

First bounded delivery: branch feat/ui-action-following-pitch-camera implements zoomed valid-source camera, smooth editorial pan, taller pitch viewport, offset actor label and unobtrusive central play overlay, with camera provenance tests. It does **not** manufacture multiple actors or ball tracking; emblem-tag wiring and selective ROI actor rendering require subsequent integrated source-data work. Editorial PR #125 remains separately open and edits App/Timeline/global CSS: avoid overlapping changes. Exact-SHA deployed screenshot still required for visual sign-off. All CI must pass; no merge without explicit approval, no Azure/Foundry paid resources.

## 17. Authoritative image comparison / broadcast realism milestone (18 Oct 2026)

The manager uploaded two explicit screenshots to the current project UI chat:
**approved target** `Neon Football Analytics Dashboard(2).png` (1672 x 941);
**pre-#128 actual** `image(20261018-202704).png` (1562 x 1266).
The images are NOT verified as tracked repository assets; future chats must
request reattachment for pixel assessment. The target is the binding
screenshot, with the already approved action-following larger ROI pitch,
source-backed actors and surname+emblem labels as explicit adaptations.

Architectural diagnosis: actual UI had its timeline and transport inside
the same central `pitch-panel`, forcing the three-column row to stretch,
while the approved hero has three similarly sized cards. Significant
differences also include missing stadium photography/lighting, compact
hero spacing and header/icon hierarchy, flat scoreboard, oversized empty
AI Insights section, and poor pitch realism.

PR branch `feat/ui-preview-fidelity-stage` (based on #128 merged SHA
`ae744fbc0c37c9003401228aee964e84b635905c`) is a coherent stage:
- `Pitch.tsx` emits a main hero pitch card and sibling under-pitch
  `pitch-replay-deck` containing unchanged real timeline and controls.
- `App.tsx` relocates optional fixture roster below primary stage,
  presents up to 3 cursor-safe real recorded match actions when tactical
  insights are sparse, and passes source-authored team emblem to the
  correctly labelled recorded actor.
- A single dedicated `web/src/brand-preview.css` is the authoritative
  layer on top of older accumulated CSS. It provides photo-backed
  stadium ambience, functional broadcast three-card proportions,
  responsive stacking, scoreboard/nav, stronger accents and depth.
- Source visual backdrop: Wikimedia Commons CC0 `Well lit soccer stadium
  (Unsplash)` by Mario Klassen, 2017. This is decoration and DOES NOT
  assert the fictional match happened there. The Wikimedia image is
  currently a remote thumbnail, with background CSS fallback;
  self-host optimized CC0 derivative before final public-scale deployment.
- `BroadcastPitchScene.tsx` improves seeded grass texture, physically
  based lighting, and fixed goalpost/net geometry; this infrastructure
  has no football-event position inference.
- Existing #128 ROI camera remains in place. Selective attacking and
  defending players still require source-aligned freeze-frame ingest as
  specified in Issue #129; no invented 22-player placements or paths.

Next reviewer must verify new frontend/Python/D2 CI, exact production
revision after manager-approved merge, and same-viewport source image
comparison. Treat PR as unaccepted until actual browser rendering is
reviewed; don't declare screenshot fidelity from static CSS review.
One focused PR at a time and explicit technical-manager merge approval.

## 18. PR #131 deployed visual audit and follow-up viewport fix (18 Oct 2026)

Current merged main: `3e787da7de4efa1eaca7041c2a0bea9e80c8b984`,
PR #131. Deployment GitHub Actions successful. Manager supplied
actual `image(20261018-211708).png` (2048x1153) alongside prior
approved `Neon Football Analytics Dashboard(2).png` (1672x941).
The stadium atmosphere and separate replay deck have improved, but
shell width is only ~68% of the screenshot versus ~94% of the target.
Pitch image clips into dark blank space near sideline actor positions.

Branch `fix/ui-broadcast-pitch-viewport-132` addresses precisely these
large fidelity gaps. The responsive desktop broadcast shell uses
~93.8% viewport width (matching the reference ratio), with no old
1568px fixed cap. `actionCameraPose` pans camera aim toward the
interior near pitch edges so source actors remain onscreen without
moving their source coordinates. The three-dimensional scene gains
an extended grass apron that is physically stadium ground beyond
the field, not invented pitch lines, players or tracked ball.
Added boundary/viewport regression tests. All old under-pitch replay
controls and sourced data remain intact. No media/AI/Foundry resource
changes. Run CI, seek explicit manager approval for any merge, then
compare with an exact-SHA deployed image at matched browser zoom and
same aspect ratio. The current screenshot is *not* visual acceptance.

## 19. Event-grounded ball marker & possession/pressure presentation (18 Oct 2026)

Owner explicitly requested visible ball and accurate knowledge of who has
possession, whether the ball is challenged, and its position. Current synthetic
`MatchEvent` has `location` of **action actor**, `possession_team_id`,
`player_id` and `evidence.under_pressure` where explicitly authored; no
independent ball tracking or duel-player locations. Even real 360 frames do
not automatically include continuous ball locations.

On branch `feat/ui-source-ball-action-context-133`, an explicit pure
`ballActionAtCursor` presentation contract shows a rendered *event-contact*
ball graphic at the **source event origin** only for carry/pass/shot/goal,
with provenance label disclosing it is NOT independently tracked ball motion.
Carry actor controls the ball at the recorded action start. Passer/shooter is
identified as initiator, not ongoing holder. Team possession is attributed
to the event clock; pressure identifies the pressing actor, no ball placed,
and `evidence.under_pressure` marks pressured action but not confirmed duel.
Turnover awards team possession but keeps ball location unknown. Full replay
seek/restart/rewind tests are required. SVG fallback matches WebGL data semantics.

Unfinished: explicit independent ball observations, exact challenged/duel
participants, real timestamped trajectories, StatsBomb historical 360 data
transport and selective source-observed attackers/defenders (Issue #129).
This milestone must not be misrepresented as continuous football tracking.
Keep the target preview's chrome/layout as implemented post-#132, no
extra Azure/Foundry charges, no merge before manager approval.

## 20. Owner-directed next workstream and actor visibility (19 October 2026)

PR #133 (event-contact ball and event-time possession/pressure) is
**merged** at `37bb23b286ce604c3889618ae1a25ee6dc6b8ecc`.
The approved broadcast preview remains binding, with the manager's
later closer region-of-interest camera, actor/player badges, under-pitch
replay controls and unobtrusive in-pitch play glyph.

**Next BLOCKED / priority data milestone: Issue #134**
https://github.com/niktolis/pitchvolt-ai/issues/134 — *integrate licensed
synchronized player and ball tracking for action ROI*. Parent UX gap
Issue #129. The Metrica Sports sample-data repo describes anonymized,
synchronized 105×68m event/tracking samples; verify the original ball
and per-player columns, synchronization, sample frequency, null/coverage
and actual redistribution rights. Its acknowledgement request is not
itself a public-hosting license. Do not silently ship upstream files,
relate different games, interpolate missing player/ball samples,
infer holder/duel state from team possession, or treat StatsBomb 360
freeze frames as continuous data. Initial work is **offline, SHA-verified
and legally gated**; explicit approval needed before hosting/inference.
The new provider-neutral schema and rendering must be separately
reviewed with tests before replacing the synthetic fixture. The
target screenshot's many players must never be fabricated.

**Next NON-BLOCKED UI bundle:** branch
`feat/ui-actor-visibility-preview-135`, after merged PR #133, delivers
a better-proportioned procedural 3D athlete at the **same exact source
event position**, a neutral unanimated representation with team color,
and a larger source-authored surname+fictional crest badge that sits
to the inward side of the actor (not on the player model).
The avatar does **not** claim to reconstruct measured body pose,
official kits, more players, or real ball tracking.
Pure edge-position tests protect badge placement; requires full CI.
This is preparation for a later multi-player source-rendering engine,
not completion of Issue #134. Keep one PR at a time, no merge without
manager approval.

Last owner-supplied actual after PR #132:
`image(20261018-213428).png`, and the approved preview is
`Neon Football Analytics Dashboard(2).png`. These screenshots must be
requested again if not present in future chat; they are not commit assets.
Screenshot CI remains intentionally disabled. Compare post-deploy exact
SHA manually at matching viewport/zoom.

## 21. Source-tracking data next step after avatar merge (19 October 2026)

PR #135 is **merged** at `7e6cdb3b83f5e856ea2589d4d3855b118668f0b0`.
The more human proportioned single recorded player, surname/fictional
team crest and side-aware badge are no longer pending.

The next major progress toward the approved 1672 × 941 preview is
**genuine observed multi-player and ball tracking**, not cosmetic
stand-in formations. Issue #134 is the execution issue (parent #129).
Upstream Metrica samples, pinned at
`e706dd506b360d69d9d123d5b8026e7294b13996`, contain anonymized
CSV Game 1/2 player+ball channels and source events; Metrica's README
does not supply explicit source redistribution permission. The current
PR branch `feat/134-metrica-offline-feasibility` is **data feasibility
only**: offline pinned SHA-256 original file integrity, Home/Away
synchronization, frame/sample/ball coverage and cross-file event joins;
synthetic-only regression fixtures and no hosted source data.

Original Metrica tracking bytes **have not been inspected** inside this
engineering runtime; do not represent format/coverage as empirically
accepted until a reviewed original-file offline report is available.
No new API player positions, no motion interpolation, no ball trajectory
or license grant is introduced. Follow-up: licensing clearance, verified
source frame audit, source-neutral observation contract and separately
approved licensed historical game replay. Keep the synthetic replay
independent, and preserve camera/replay controls/hero layout.

See `docs/architecture/metrica-tracking-feasibility.md`. All required
CI and explicit manager merge approval apply. Do not invent a screenshot
capture or say visual acceptance is complete.

## 22. Post-#136 visual milestone: cinematic source-backed Key Moment (19 October 2026)

PR #136 merged at `37de0d762f7fdb1df37509c4a55ddcbd4dd45a5c`.
The merge incorporated post-review tracking safeguards: canonical upstream
Metrica Git-blob identity verification, strict source file bounds, and
period/frame joining. This is still an **offline audit only**, not an
authorized published real-match tracking replay. Foundry PR #137 has also
merged; preserve its independent workflow/CI hardening.

Current UI branch `feat/ui-key-moment-source-3d-138` addresses the
approved reference's right-side **Key Moment cinematic treatment**. It
replaces the previous flat 2D-only Key Moment card with a closer
source-anchored THREE.js render of the **same** selected MatchEvent:
the existing neutral 3D actor, team-color kit, known player surname,
fictional emblem, measured field markings, decorative turf, fixed goals
and, only for applicable source actions, the event-contact ball marker.
The camera is *editorial framing*, not source video or player tracking.
Both central pitch and right-side moment use the same replay clock; no
second event stream, team movement, possession inference or invented
teammates are introduced. The card explicitly labels itself 3D
editorial reconstruction and retains original SVG when WebGL is absent.

Implementation reuses the existing mesh components from
`BroadcastPitchScene.tsx`, and runs the small Key Moment Canvas
`frameloop="demand"` (not a second continuous 60-fps renderer)
to limit WebGL resource use. Unit tests cover camera source anchoring,
invalid/missing observations and field corners. No new npm packages,
photographs, logos or media rights. Preview screenshot remains the sole
visual spec; **do not claim exact fidelity before a real deployment SHA
and measured same-viewport screenshot**. This does not close Issue #134,
which remains blocked on licensed original tracking data.

Run frontend, Python and architecture CI; make PR reviewable only when
all green; never merge without explicit approval.

## 23. PR #138 merged; Key Moment analysis CTA remains usable before AI publication (19 October 2026)

Verified `main` `946caf4c9006c3aa0160d099d17cbabac6dc2725`:
PR #138 cinematic source-backed 3D Key Moment merged. Independently
PR #139 (provider-neutral tracking contract) was already merged at
`3fa7d684a60e2e91274a71ee2d68e50d0b257f89`.
A validated tracking **schema is not source samples or a right to
redistribute**: multi-player/ball tracked UI remains separate and gated
by Issue #134 licensing and data availability. On first check the
#138 deployment workflow had not completed; do not claim production
visual fidelity until exact deployed SHA and manager screenshot.

Next **non-blocked UI functionality** branch
`feat/ui-key-moment-action-details-140`: the prominent target-preview
"View Analysis" button was disabled until a published tactical insight.
It now preserves the existing published-insight navigation, but when
only a real recorded MatchEvent is available it opens a source-only
recorded-event facts overlay inside the Key Moment card. This does NOT
generate AI or claim tactics. The panel lists observed action time,
event type, actor/team, source outcome, recorded possession-team-at-event,
valid actor coordinates and valid action destination, with explicit
individual-holder/ball/pressure/contest unknownness. For `carry`
alone, a source-authoritative owner may be named at the event instant;
for `pressure`, the opponent pressing is **not** the possessor.
It is invalid to infer ball flight, challenge outcomes or team press
strategy. The overlay includes a close control and preserves the
approved three-column card height, stadium photo, 3D pitch and
under-pitch real replay controls. Seeking backward hides future
event-specific details rather than leaking source records.

Run full frontend/TypeScript/Vitest/Python/architecture CI, maintain
green checks, request manager review. Do not merge without approval.
Source screenshot remains binding; next deployment manual screenshot
must verify both new 3D panel and functioning CTA.

## 24. Key Moment 3D fidelity pass after merged PR #141 (19 October 2026)

Verified main SHA `e28eac6f40963888ee3f9b593bd1c6e4f31c3ee5`,
PR #141 **merged**. The existing Key Moment View Analysis CTA is now
usable before and after AI insight publication, with evidence-safe facts
and no false ball ownership. #141 deploy was pending when initial check
was performed; do not claim exact production screenshot verification.

The user requested **EA FC-quality** Key Moment visuals while respecting
our approved application preview and stricter source-backed football
positions. The after-#138 screenshot showed a still simplified green
scene, low-poly player, thin lighting and minimal depth.

PR branch `feat/ui-key-moment-render-fidelity-142` is the next
non-blocked presentation milestone:
- Add a standalone medium-detail **art-directed 3D hero avatar**,
  `KeyMomentAthlete.tsx`, using physically shaded/cloth-bumped kit
  material, rounded anatomy, face/football apparel/boots, and generic
  body poses keyed to recorded event **type only**. Those poses are
  *illustrations*, not observed joints or genuine player motion.
- Key Moment remains at exact source actor `toWorld(location)`
  and validated heading; no invented players/defenders/ball flight.
- Improve low-angle, tighter Key Moment camera, ACES tone mapping,
  directional key/fill/rim floodlight, 1024px single shadow map,
  one-shot 256px contact shadow, and reproducible **1400-blade single
  instanced turf draw call** near the source-actor ground point.
- Preserve demand frame-loop, SVG fallback and the source-only ball
  event-contact rules from PR #133. No new npm dependencies, backend,
  Foundry billing or Azure resources.
- Add camera/pose regression tests and manual deployment screenshot
  acceptance. The eye-catching illustrations remain explicitly labelled
  art-directed 3D portraits, NOT real video or sampled human pose.

**Important fidelity ceiling:** procedural meshes cannot truthfully be
declared AAA game photorealism. A separate Issue #142 covers verified,
self-hosted optimized CC0 soccer avatar GLBs/LODs, material and licensing
validation, GPU performance and explicit asset manifests. Innerscene
offers CC0 ~17.5MB/112k triangle soccer figures (standing/running/kicking)
but their GLBs and runtime cross-origin behavior were not validated in
this engineering environment; do not make production hotlink them.
Issue #134 still tracks real licensed multi-player/ball match tracking,
independent of the hero-avatar/rig asset choice.

Never label preview visually accepted from CI alone. Seek exact
deployment SHA and a fresh manager screenshot after merge. No merge
without manager approval.
