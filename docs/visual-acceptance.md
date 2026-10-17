# PitchVolt visual acceptance

## Authoritative target

The **Application Preview** panel in the approved PitchVolt AI brand guide is the sole visual target. Do not substitute alternative mockups or reinterpret its colors, navigation, scoreboard, panel proportions, pitch, typography, branding, or artwork without explicit approval.

## Automated deployed-browser evidence

After the existing Azure deployment and health check complete, the GitHub Actions **Deploy Azure Container App** workflow runs the independent `visual-evidence` job. It opens **https://pitchvolt.app/** in headless Chromium, checks that the broadcast grid and pitch exist, waits briefly for font loading and replay startup, and captures full-page screenshots at **1600 × 900** desktop and **390 × 844** mobile viewports. Download the `pitchvolt-live-visual-<commit>` artifact from the Actions run.

These are **real live-page screenshots**, not mockups. They are intentionally *not* automated pixel-perfect pass/fail checks: live SSE, fonts, and latency make screenshots non-deterministic. An artifact's existence does not establish approval or compliance with the brand preview.

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

The local script requires network access to the public site. Browser capture doesn't mutate Azure resources or use Foundry inference. The live-domain workflow requires the Azure managed certificate and DNS binding to remain valid.

## Exact production-revision gating

Production HTML has a `pitchvolt-build` meta tag populated from the immutable Git commit at container image build time. Following `/health`, the deployment workflow polls the public `pitchvolt.app` homepage with a cache-busting query until the tag matches `GITHUB_SHA`; a stale previous revision is not considered deployed. Browser screenshot capture independently checks the same exact SHA before writing evidence. If the public hostname fails to converge, the deployment fails visibly and no screenshot job runs. This verifies revision identity, **not** visual fidelity or complete correctness.
