# MatchPulse AI — durable project handoff

**Updated:** October 15, 2026. **Hackathon submission deadline:** October 27, 2026.
This file is the first document to read when continuing development in another ChatGPT project conversation. Prefer the current `main` branch and open issues/PRs over stale chat summaries.

## Project and guardrails
- Repository: https://github.com/niktolis/matchpulse-ai (private during implementation; publishing may be required for submission). GitHub Project board: https://github.com/users/niktolis/projects/6 (issue board management unavailable in current connector).
- Challenge: synthetic Premier League-style match intelligence and personalized, evidence-backed broadcast storytelling. Required phases: Ingest → Interpret → Explain → Render → Personalize.
- Five equal judging criteria (20% each): Technological Implementation; Agentic Design & Innovation; Real-World Impact & Applicability; User Experience & Presentation; Challenge Adherence.
- Hard budget: **zero out-of-pocket**, use only Azure Free Trial credit (€175.99 displayed on October 15, 2026, trial spending limit On). Explicit approval required before provisioning billable Azure services. User created RG `rg-matchpulse-dev`, Foundry account `matchpulse-ai-resource`, project `matchpulse-ai` in `swedencentral`. At inspection there were no model deployments.
- **DRY governs architecture, design, tests, docs and code.** Canonical event schema and single tactical processor; provider-neutral adapters; no duplicate metrics in AI prompts/UI.
- Git workflow: issue-backed feature branches, draft PRs, green tests/architecture D2 render, **owner review and approval before merging**. No automatic Azure provisioning.
- Codex interaction approved **specifically for MatchPulse AI**, not any unrelated repo or organization.

## Approved architecture decisions
- ADR-0001 deterministic match intelligence owns metrics/state/evidence; AI only explains personalized verified facts.
- ADR-0002 selectively orchestrated Analyst and Storyteller roles; always-on deterministic claim verification; conditional Editorial agent. One orchestrator, not three hosted services; record traces and cost/latency comparisons.
- ADR-0003 container-native Azure Container Apps Consumption target instead of AKS; two-speed design: immediate deterministic overlays, asynchronous selectively triggered Foundry storytelling.
- Data: **original synthetic events only**; StatsBomb open data as *reference* subject to licensing, not distributed actual Premier League events. Wyscout excluded; socceraction/Kloppy not a dependency. Canonical provider-neutral Pydantic schema and minimal EventSource port.
- Playback: SSE one-way for MVP; HTTP for replay control/evidence; WebSocket only if genuinely required.

## Implemented through PR #12 (merged)
- `src/matchpulse/events.py`: versioned canonical event model and stream integrity.
- `src/matchpulse/simulation.py`, `scenarios.py`: seeded fictional high-press, counterattack and sustained-possession test fixtures.
- `src/matchpulse/intelligence.py`: stateful deterministic processor, classifications of high press and counterattack; sustained possession remains negative control rather than implemented detection.
- Python dependency locking with `uv.lock`, CI `uv sync --frozen`; Python/uv Docker image digests pinned; Docker Compose, Dev Container and shared `scripts/check.sh`.
- D2 under `docs/architecture/diagrams/`, auto-generated SVGs embedded in architecture README, PDF/PPTX export through shared `scripts/render-architecture.sh`. D2 version v0.9.0.
- Do not describe Python fixture simulator as full-match or physical realism, nor assert deployed services exist.

## PR #13 — real-time API (this change)
- `src/matchpulse/api.py`: FastAPI health, scenario catalog, completed-fixture state, evidence lookup, replayable finite SSE with speed and resume cursor.
- `tests/test_api.py`: API/contract, replay ordering, Last-Event-ID, bad requests, evidence.
- Runtime container serves Uvicorn on port 8000; CI performs actual HTTP smoke test.
- New dependencies fastapi, uvicorn and dev httpx included in committed lock; CI must remain green.
- `docs/architecture/realtime-api.md` describes limits. Diagrams updated to show real transport and planned Foundry/UI.

## Next priorities after PR #13 merges
1. **Live React/TypeScript broadcast UI** subscribing to SSE; show football pitch, actual sourced event markers, tactical overlay, playback modes and visible evidence panel.
2. **Foundry agentic workflow** using read-only match/evidence tools, Analyst → Storyteller, deterministic claim verification, optional Editorial, token budgets and structured output schemas. Compare with baseline.
3. Complete-match simulator/multiple causal scenarios; sustained-possession detector and measurable tactical analytics.
4. Azure Container Apps/Bicep deployment **only after cost estimate and owner's explicit approval**; no free-trial upgrade; prepare accessible judging demo.
5. Additional language, club/player view, recap and demo video; ensure submission ready by Oct 27 and available for judging through Nov 10, subject to credit/expiry check.

## Local commands
```sh
uv sync --frozen --extra dev
uv run --frozen bash scripts/check.sh
uv run --frozen uvicorn matchpulse.api:app --reload --port 8000
curl -N 'http://localhost:8000/api/matches/high_press/stream?speed=1000'
docker compose build backend
docker compose run --rm backend bash scripts/check.sh
bash scripts/render-architecture.sh --check
```

Read `docs/architecture/README.md`, `docs/architecture/realtime-api.md`, `docs/development.md` and current GitHub issues #1–#8 before changing interfaces or scope. Every PR should describe the business logic with concrete code examples and update static/dynamic D2 architecture plus rendering.

## October 16 update — StatsBomb-shaped synthetic input (issue #15)

PR #14 (React UI) merged into main at `345ba2c81f8bafc60f84597311436eb7dd3f6b9d`. Issue #15 tracks strict synthetic StatsBomb-shaped adaptation and future full Open Data compatibility. A subsequent unmerged feature PR may add the 120 × 80 → 105 × 68m coordinate transformation, original synthetic source/adapter, and the `statsbomb_high_press` demo. The canonical source-of-truth model, single tactical processor, evidence and React pitch continue to use 105 × 68 **metres**; no real historical data may be mislabeled synthetic. Check the actual PR and main status before resuming. Foundry issue #4 remains the highest-priority agentic milestone.
