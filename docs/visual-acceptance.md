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
