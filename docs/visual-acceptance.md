# PitchVolt visual acceptance

## Authoritative target

The **Application Preview** panel in the approved PitchVolt AI brand guide is the sole visual target. Do not substitute alternative mockups or reinterpret its colors, navigation, scoreboard, panel proportions, pitch, typography, branding, or artwork without explicit approval.

## Manual, opt-in deployed-browser evidence

Browser screenshots are intentionally **not** captured by any GitHub Actions
deployment job. The prior `visual-evidence` workflow job was removed because
an automatic screenshot immediately after rollout did not provide useful
review of the actual visible page. It added expensive browser installation
and runner time with no reliable human-approved visual comparison.

Capture desktop and mobile only when an operator chooses to validate a
verified deployed release using the existing local script below. Keep
the approved Application Preview image as the sole visual target, and do not
declare acceptance from an artifact's existence alone.

## Review checklist

Compare each screenshot manually against the approved Application Preview: logo asset and spacing; stadium header; scoreboard treatment; active navigation; 3-column AI Insights / tactical pitch / Key Moment composition; Volt-green palette; pitch illumination and dimensional players; typography; borders, alignment, and spacing. Document deviations as actionable issues and only mark acceptance after a human review.

The replay must never fabricate club crests, match scores, lineups, player positions, or AI analysis to fill the mockup. Source-backed functionality may require visibly honest placeholders until its underlying data is implemented.

## Local reproducibility

Install Playwright in an isolated Python environment and Chromium, then run:

```shell
python -m pip install playwright==1.58.0
python -m playwright install chromium
python scripts/capture-live-visual.py --url https://pitchvolt.app/ --output artifacts/visual
```

The local script requires network access to the public site. Browser capture doesn't mutate Azure resources or use Foundry inference. The deployed site still requires its Azure managed certificate and DNS binding.

## Exact production-revision gating

Production HTML has a `pitchvolt-build` meta tag populated from the immutable Git commit at container image build time. Following `/health`, the deployment workflow polls the public `pitchvolt.app` homepage with a cache-busting query until the tag matches `GITHUB_SHA`; a stale previous revision is not considered deployed. The optional local screenshot script can check the same exact SHA with `--expected-sha`. If the public hostname fails to converge, the deployment fails visibly; **no automatic screenshot job runs**. This verifies revision identity, **not** visual fidelity or complete correctness.

## 18 October 2026 — authoritative side-by-side reference freeze

The technical manager re-uploaded the **approved exact target image**
`Neon Football Analytics Dashboard(2).png` (1672 × 941 pixels) and the
**pre-PR-#128 actual production screenshot**
`image(20261018-202704).png` (1562 × 1266 pixels).
These are conversation attachments, not yet copied into this repository;
request both again if not available in a future session. The target
remains binding even if a subsequent screenshot or implementation differs.

Target: wide photographic night stadium and floodlights; dark translucent
broadcast navigation/header; monumental team scoreboard; narrow active
tabs; three compact similarly tall **AI Insights / Tactical Pitch /
Key Moment** cards in the first viewport. The pitch is the largest card
and is required to support the manager's later **source-action ROI camera**
rather than a permanent full-pitch overhead picture. Source surnames and
authorized fictional badges appear alongside players, not over them.
Replay event rail and real playback controls remain visibly below the
central pitch, but MUST NOT make the three hero cards taller by sharing
the hero grid row. Roster/evidence tooling may appear further below.

Pre-#128 actual: minimal gradient/floodlight placeholders rather than a
real stadium, no high-fidelity crowd background; scoreboard/header too
flat; central 3D pitch appears small within a large dark viewport;
one source actor only; central card stretched hugely by nested activity
timeline/transport; side cards stretch with it; sparse live insights.
Never fabricate analyses, player/ball positions, club trademarks or
action photographs to fill these gaps.

**Visual foundation implementation** separates the center stage from
the replay deck into two explicit grid rows, relocates the expandable
roster below the main hero, uses consistent brand contrast and sizing,
introduces a CC0 decorative stadium image, and improves source-action
grass/goals/stadium lighting. The real photograph is decorative only and
does NOT portray the fictional fixture, its crowd, or current event.
Author/source: Mario Klassen, 2017, `Well lit soccer stadium (Unsplash)`,
Volksparkstadion; CC0 1.0 via Wikimedia Commons:
https://commons.wikimedia.org/wiki/File:Well_lit_soccer_stadium_(Unsplash).jpg
The CSS references a 1280px Wikimedia thumbnail with a dark CSS fallback.
For a mature deployment, self-host an optimized licensed derivative with
provenance metadata instead of relying on the Wikimedia asset CDN.

**Review gate:** validate the exact newly deployed Git SHA, recapture
same viewport (recommended 1672 × 941) after browser cache refresh, then
quantify header/sidebar/center/pitch/CTA differences. Frontend CI is not
screenshot or pixel-match acceptance. No new external runtime AI model
inference or fictional player tracking is approved.

## Post-PR #131 actual screenshot comparison — 18 October 2026

The technical manager uploaded a current screenshot
`image(20261018-211708).png` at **2048 × 1153** following the
successful deployment of PR #131 (merged main
`3e787da7de4efa1eaca7041c2a0bea9e80c8b984`). The authoritative
reference remains `Neon Football Analytics Dashboard(2).png` at
**1672 × 941**. These are conversation attachments; they are not
tracked repository images.

Measurable primary discrepancy: screenshot broadcast shell occupies
approximately 68% of screenshot width, versus ~94% in the approved
preview. Browser zoom/scaling cannot be established from the screenshot
alone; the stylesheet did impose a 1568px fixed maximum. The next
stage changes the desktop shell to 93.8% viewport width at the
reference size, retaining responsive mobile layouts.

The 3D field also occupies only the upper part of the center viewport,
leaving an extensive black lower region when the current source actor
is close to a field edge. The camera was aimed directly at the recorded
actor even if it sat on a touchline, revealing WebGL void beyond the
105×68m measured field. The follow-up clamps *camera aim only* within
the source field, keeps the actor itself at its exact source position,
and renders non-playable dark textured turf beyond the boundary as
fixed **stadium infrastructure**, not a claimed playable/tracked area.
Regression tests cover goal-line/touchline actor visibility and
screen ratios.

The remaining high-priority divergence is player/crowd realism and the
number of visible *observed* action participants. Source snapshot work
from Issue #129 remains mandatory; no illustrative teammates or
ball can be inserted. After merge, compare desktop at the same aspect
ratio and browser zoom, using a cache-busted deployment SHA and
screenshot before claiming visual acceptance.

## Event-based ball symbol is not continuous tracking (18 October 2026)

A ball symbol may appear in the 3D viewport only at the source-recorded
origin of a carry/pass/shot/goal. It is an **event-contact marker**, not a
separately observed ball position or a promise of animation: the canonical
record contains no ball tracking. A label gives possession **at event time**
and identifies the carrier **only for carry**; passes and shots name the actor
who initiated the contact. Defensive pressure/turnover events have no ball
marker; a documented pressured pass is not automatically a tackle or duel.
The status panel stays legible but subordinate to the approved pitch.
Validate paused/play/rewind, explicit unknown/pressure statuses and SVG
fallback in exact deployed snapshot after merge; source-clocking tests
must pass before review.

## Post-#136 Key Moment treatment — proposed PR #138 (19 October 2026)

The approved target image depicts a cinematic Key Moment, while the
deployed application still uses a diagrammatic overhead 2D pitch.
A generic football action photograph would misrepresent the fictional
source event unless an independently verified same-match image existed.
Instead the new **close-up 3D reconstruction** reuses the *recorded*
event's player and action-time source location in the existing renderer.
It displays only one independently positioned avatar; ball-contact
graphic is event-origin illustration and not sampled trajectory;
fixed grass and goals are environmental infrastructure. Team colors,
fictional emblems and player label come from current source presentation
metadata, never guessed from the reference photograph.
The Key Moment camera is editorial; replay-time/cursor bounds are
identical to central pitch. WebGL unavailable or invalid actor retains
the original SVG fallback. A visible provenance label differentiates
the reconstruction from video or a live camera.

For visual approval, compare the actual deployed SHA in the browser
at the approved viewport and verify the actor appears in-frame at
sideline and goal positions, the label does not obscure the avatar,
the recorded ball only appears for documented actions, and no
second continuous render loop degrades playback or mobile performance.
This PR cannot be marked pixel-faithful from unit tests alone.

## Post-#138 UI action details without invented AI (19 October 2026)

The approved preview has a prominent working right-side
`View Analysis` CTA. In the existing implementation the CTA was
disabled when no published tactical insight existed, even though
the replay already provided source-recorded event facts. This is
a user-visible mismatch. The next UI branch makes that control
functional: when published insights exist, navigate to them as
before; otherwise open an overlay within the same Key Moment
card with only observed event fields and explicit unknown
possession holder / ball trajectory / challenge semantics.
No new LLM call, player coordinates, score, generic football
photo, or tactical assertions. Test at early event time, after
insight publication, on seek/rewind, and at different viewport
widths without stretching the card. The cinematic 3D scene
and approved card appearance remain unchanged when overlay
is closed. Exact-SHA production screenshot comparison is
still required after merge.

## High-fidelity Key Moment after PR #141 (19 October 2026)

Manager's current actual screenshot: `image(20261019-082157).png`
in the conversation, showing a lone simple low-poly avatar and flat
grass in the right-side 3D panel. Authoritative target remains the
`Neon Football Analytics Dashboard(2).png` 1672×941 brand preview.
Explicit request: aim for realistic premium EA FC-like rendering
quality, while maintaining source-grounded match events.

Visual pass on branch `feat/ui-key-moment-render-fidelity-142`
uses a more detailed original 3D art-directed human silhouette,
woven kit fabric shading, skin/hair/footwear anatomy, stronger low
stadium lighting and shadow definition, a closer ~4.3m hero camera,
seeded fine-grass instancing and cinematic vignette. The current
event's exact 105×68m canonical location/valid orientation is
unchanged. Art-directed strike/stride/defensive postures are **not**
measured poses; public label must disclose the difference.
No licensed EA/FIFA/club/real-player assets, cross-fixture players,
source-nonexistent ball trajectories or tracking claims are added.
Demand rendering and fallback remain mandatory.

Manual acceptance on deployed SHA: actor should occupy substantially
more vertical space, remain within the 16:9 Key Moment at every
field corner, receive plausible localized shade and contact shadows;
second WebGL view must not trigger continuous 60FPS repaint or mobile
performance regression; verify normal/light/dark DOM readability,
WebGL-off SVG path, action/event changes, replay rewind, hover/keyboard
CTA overlay and actor identity badges. CI is not screenshot acceptance.
A separate Issue #142 is required for optimized, self-hosted high-detail
CC0 GLB assets; do not claim this self-contained procedural pass
matches full AAA realism.

## Optional licensed footballer GLB stage after PR #143 (19 October 2026)

The currently approved deployed target still needs externally
verified realistic football player meshes. Branch
`feat/142-verified-hero-asset-pipeline` introduces an **opt-in
binary asset integration contract**, with an empty default manifest.
Thus its UI must remain identical to post-#143 until an actual
locally inspected, optimized, independently SHA-pinned original
CC0 soccer-player GLB is bundled on a further reviewed PR.
Do not claim a visual improvement merely because model selection
and CDN-free loading exist. Validate self-hosted asset size and
kit material; no team official kit, ball tracking, realistic joint
samples or extra field players may be assumed from a static GLB.
Review standalone GLB provenance, manifest digest, mobile budget
and exact-SHA browser screenshot before accepting visual fidelity.
Approved target screenshot remains authoritative; start from the
same 3D cinematic Key Moment camera and source-only positional truth.

## Real CC0 footballer — source-pinned 3D asset visual acceptance (19 Oct 2026)

PR #148's asset framework is merged, and the first **actual optimized,
self-hosted, independently source-hash-pinned** GLB has been added
to branch `feat/142-cc0-real-footballer`:

- Innerscene "Soccer player, standing" (MakeHuman-based CC0 1.0).
- Original 18,349,744 B, SHA-256
  `773cfa73bbcf659d7044934aaeacf1c3c9a49ae2955a51f56de7ad61ad1b6ffb`.
- Optimized 2,583,972 B, 70,839 triangles / 13 meshes, SHA-256
  `5bb8a63f2824d84c4f8a346ca11d6af0eefd1854050cfa3dde4fb12a134c6591`.
- Art-directed anonymous **standing** player replaces the placeholder
  only in the 3D Key Moment scene; source match event location and
  canonical camera stay identical. Other action categories use the same
  verified neutral model until action-specific figures are licensed
  and loaded separately.

**Not yet visually accepted:** Need real deployed-SHA screenshot at
reference 1672×941 and typical 16:9 desktop, correct feet-on-turf
orientation, believable scale in 3D hero camera, factual event actor
badge unobscured, team-color top material (both fictional colors),
consistent model texture lighting and backup procedural player for
WebGL/GLB failure, no continuous WebGL repaint or mobile stalls.
This is a standing static portrait, *not* a sampled athletic skeleton,
animation, production photorealism or measured ball trajectory.
Do not declare EA FC equivalence from asset validator/CI alone.

**Extra GLB fidelity check:** The official standing player asset contains
a decorative static soccer ball and jersey-number object. Both are
suppressed as unobserved match props. Inspect a possession-free/pressure
frame for zero decorative ball, and verify the separately sourced
ball-contact indicator is the only allowed ball graphic. Do not show
invented shirt numbers or branded kits.

## Source-safe Key Moment post-#151 correction: duplicate ball and poses

The 19 Oct screenshot shows a **double football** at the source
actor and mannequin-like standing pose even during carries. The
approved follow-up replaces imported assets with a source-verified
**same-character** trio: standing (neutral), running (carry/pressure),
kicking (pass/shot/goal). The entire original embedded soccer ball
and unsupported shirt-number **render graph nodes** are detached
from every shipped GLB, tested both offline and in CI. The source
event-contact ball remains the only eligible illustrated ball.
A tighter camera frames the athlete more prominently. No movement
path, opponent position, player skeleton tracking or true footage
is implied; action-category pose remains editorial/static.

Do not accept from CI alone. After exact deployment SHA, capture
the full approved 3-column reference-sized layout and at least:
1. A carry at the actor source location with one or zero eligible
   ball-contact symbols, no extra rendered model ball.
2. A pass/shot portrait in a static kicking stance, same character
   face, hair and team-color style.
3. A pressure/turnover event without ball geometry when the source
   does not document event contact; none attached to the model feet.
4. Mobile/narrow viewport with no cropped torso/head, intact
   replay controls, fallback and badge not obscuring player.

If a source-relative sporting pose is not visually credible,
adjust static art direction or camera in a subsequent PR after
review; do not add fabricated continuous tracks.
