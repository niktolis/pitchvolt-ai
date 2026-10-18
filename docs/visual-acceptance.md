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
