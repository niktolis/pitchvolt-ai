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
