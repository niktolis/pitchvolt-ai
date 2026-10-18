# PitchVolt AI — durable handover for the next ChatGPT project conversation

**Last updated:** 18 October 2026. **Hackathon deadline:** 27 October 2026.
**Canonical repository:** https://github.com/niktolis/pitchvolt-ai
**GitHub Project:** https://github.com/users/niktolis/projects/6
**Production:** https://pitchvolt.app

> **Start any next chat by reading this file and inspecting live GitHub main,
> open issues, open PRs and CI. Do not rely on historical conversation memory
> instead of the repository. This document is committed as part of each
> substantial implementation bundle and must be updated before handover.**

## Operating contract / safety

- One bundled PR at a time, branch from current `main`; run Python tests,
  frontend build, schema/OpenAPI regeneration checks, and D2 architecture CI.
  Ask for technical-manager review before merge; **do not automatically merge
  a PR** merely because CI passed. After approved merge, provide a concise
  report: architecture, business behavior, tests, risks, next implementation.
- Keep Python/domain/React/Docs DRY; maintain exact generated OpenAPI↔TS
  contracts and D2 source and checked SVGs. No duplicated football logic in UI.
- **Strictly source-backed player positions.** No illustrative team formation,
  invented 22-player tracking, arbitrary ball position, guessed identity,
  off-field coordinate clamping or extrapolation. StatsBomb 360 is sparse,
  anonymous freeze-frame observations, not full-match tracking.
- Historical StatsBomb Open Data is **real historical data**, never synthetic,
  and original JSON remains offline until license/redistribution/attribution
  rights are reviewed. Match ID/commit/digest must agree.
- No new billable Azure services, Foundry deployments/inference, subscription
  quota changes or spending without **separate explicit approval**. Trial
  budget notifications are not a hard stop. The Foundry runtime is hard
  disabled on the public server; local explicit live smoke is billable.
- Never enable Codex in GitHub orgs without explicit approval, especially
  `cariad-t2`. Respect PitchVolt's existing GitHub connector scope.
- **Visual target:** the approved PitchVolt Application Preview screenshot,
  not a generic alternative. Keep play/pause, speed, seek and replay controls
  below the pitch. Manual browser visual review **only after** deployment and
  exact revision verification; automated `visual-evidence` job was removed.

## Verified deployed baseline — check fresh main

- Repository rebrand and GitHub rename completed. Existing legacy-named Azure
  resource group `rg-matchpulse-dev`, Container App `matchpulse-web`,
  ACR `matchpulsea433a4e04d` deliberately retained. GitHub→Entra
  immutable OIDC credential `pitchvolt-main` verified.
- At creation of this handover update, `main` was
  `6f7536530effe1646cc8ee2beba9229d17991bdc`
  (merged PR #115). Production GitHub run #39152080404 succeeded:
  `verify` + `build-deploy`, exact public revision and HTTP GET health.
- Toolchains: Node **26.10.0** in `.node-version`, immutable Docker
  Node image, Node 24-native GitHub Actions, Ubuntu 24.04;
  `visual-evidence` deployment job removed.
- React 19, TypeScript, Vite, Three.js/R3F/Drei; broadcast UI has working
  pitch, replay clock/seek, evidence and narrative view. Current source
  positions have **one source-recorded actor per synthetic event**, not a
  22-player continuous lineup. Scoreboard deliberately shows unavailable.
- FastAPI/Pydantic, synthetic scenario registry with short high press,
  counterattack, sustained possession, StatsBomb-shaped *fictional*
  high-press and `extended_match`: 220 original-fiction actions, two halves,
  reaches 90:00; deliberately scripted 2 high-press, 1 sustained possession,
  1 counterattack tactical insight. Data distributions are **not** a
  physically realistic calibrated full-match simulator.
- MatchProcessor deterministic insight/evidence; /timeline finite snapshot,
  /stream replay SSE, /state, /evidence, independent local narrative SSE.
  The React replay consumes immutable /timeline for seek and client clock.
  Microsoft Foundry agents/tools and offline tests exist, but public
  inference remains disabled, authored free prose is shadow-only.
- StatsBomb historical source files for 9880 and 3764440 were verified in
  independent ephemeral GitHub audits, NOT committed; verified match 3764440
  has 4160 events and 3914 360 frames; **only 8 frames (0.20%)** observe
  eleven on each side and non-actor detections are anonymous. The local
  `--full-xi-gallery` inspects them OFFLINE. Continuous 22-person rendering
  is not supported by this source.

## Current active PR — validate before proceeding

- **PR #116**: https://github.com/niktolis/pitchvolt-ai/pull/116
  `feat/66-unified-replay-source-contract`, issue #66 (P0).
  Status when authored: **draft / unmerged**.
- Bounded scope: `src/pitchvolt/replay_dataset.py` introduces read-only
  `ReplayDataset`, `ReplayAction`, `ReplayCursorSnapshot`,
  `SyntheticReplaySource` and `HistoricalReplaySource`. Synthetic
  fixtures preserve exact canonical MatchEvent + independent SHA fingerprint;
  historical projection preserves original source manifest and omitted event
  families but never creates synthetic MatchEvent or invokes MatchProcessor.
  `api._load` must use SyntheticReplaySource **without changing public
  endpoint/SSE wire contracts**. Python fixture/source/cursor tests and docs.
- First check PR head + CI, fix any failures, verify source/provenance,
  zero future insight leakage, and explicitly seek user review **before merge**.
  No historical endpoint/asset redistribution or paid inference.
- `docs/architecture/replay-data.md` defines exact behavior and limitations.
  All files in the PR must be checked; this handover text may have been
  written before CI completed.
- #66 cannot be closed until presentation, score, roster, substitution and
  client contract integration are delivered. Do not call this first slice
  full historical interoperability.

## Next prioritized implementation, after review/merge of #116

1. **#59 + #60**: Provider-neutral validated match/team/roster metadata and
   replay-time event-sourced score/substitutions, **without inventing
   kickoff score for excerpts**. The synthetic canonical model has no
   substitution event yet; source-derived state must be explicit. Original
   fictional crests need design approval. Generated OpenAPI↔TS contract and
   scoreboard, team colors and actor surnames only after validated facts.
2. **#63 + #58**: Canonical source/insight/narrative cursor semantics, no
   future leakage after seek/rewind; no stale async evidence or narrative
   updates on scenario/mode change. Continuous action ticker backed by
   MatchEvent, tactical insights remain separate.
3. **#4**: real Microsoft Agent Framework / Foundry Analyst (GPT-5 mini),
   Storyteller (GPT-4o mini) verified inference and handoff, only after
   individual approval and cost/usage review. Live smoke history exists in
   `docs/architecture/controlled-narratives.md` and
   `docs/architecture/foundry-smoke-test.md`: successful 6/6 read-only
   Analyst evidence retrieval and structured specialist outputs in one test,
   but incomplete `fact_order` forced correct fallback. Prior GPT-5 mini
   token exhaustion and SDK issues are documented. Do not claim successful
   publication of arbitrary AI prose or rerun billable tests without consent.
4. **#18 + #61**: fidelity to approved visual layout with source-only pitch
   markers, validated team colors/fictional crest IDs, broadcaster UI,
   responsive replay controls. Manual compare deployed exact SHA to target.
5. **#8 / #31 / #6**: pre-submission validation, measured latencies,
   performance/telemetry, Foundry cost evidence, 60–90s video, README,
   judging traceability, legal/source audit. Submission freeze Oct 25–27.
   P2 multilingual recap #7, public Pages #26 and complete Open Data
   ingestion #64/#15 can be deferred if demo/core proof is threatened.

## Concrete repo entry points and checks

- Source: `src/pitchvolt/replay_dataset.py`, `events.py`,
  `intelligence.py`, `scenarios.py`, `extended_fixtures.py`,
  `providers/statsbomb_historical.py`,
  `providers/statsbomb_projection.py`,
  `providers/statsbomb_360.py`, `api.py`, `narrative_stream.py`.
- Browser: `web/src/App.tsx`, `web/src/domain/replayClock.ts`,
  `web/src/components/Pitch.tsx`, `BroadcastPitchScene.tsx`.
- Architecture: `docs/architecture/README.md`,
  `docs/architecture/replay-data.md`,
  `docs/architecture/pitch-rendering.md`;
  `docs/judging-traceability.md`, `docs/statsbomb-baseline.md`.
- Local fish/bash:
  `uv sync --frozen --extra dev`,
  `uv run --frozen bash scripts/check.sh`,
  `npm ci --prefix web`,
  `uv run --frozen bash scripts/check-web.sh`,
  `bash scripts/render-architecture.sh --check`.
- GitHub Project: update issue statuses/labels and exact PR links after
  successful implementation; keep README and handoff in sync.

**Next-chat prompt:** "Continue PitchVolt AI from
`docs/handoff-next-chat.md` on `niktolis/pitchvolt-ai`. First inspect
main, PR #116 and issues #66/#59/#60/#63/#4; finish the in-progress
one-PR bundle with green CI and my explicit merge approval, then advance
the prioritized roadmap. Strict source-backed player positions only;
no paid Foundry inference without explicit approval; update this handover
before switching chats."
