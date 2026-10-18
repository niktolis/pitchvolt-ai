# Live broadcast UI — behavior and architecture

> **Continue UI work in a new chat:** read the [dedicated UI handoff](../handoff-ui-next-chat.md) alongside the [overall project handoff](../handoff-next-chat.md). The UI handoff records the approved preview, source-position safeguards, PR #117 state and manual visual acceptance protocol.

## Business purpose

The React broadcast is the first judge-visible vertical slice of PitchVolt AI. It turns the deterministic replay transport into an inspectable experience without creating a second source of football truth:

1. **Ingest** — FastAPI publishes canonical `MatchEvent` and deterministic tactical-insight messages over SSE.
2. **Interpret** — `MatchProcessor` remains the only component that classifies high press or counterattack and calculates metrics.
3. **Explain** — the current UI uses deterministic wording derived from the verified insight payload. Microsoft Foundry storytelling is intentionally not represented as implemented yet.
4. **Render** — React projects canonical 105 × 68 metre coordinates onto the pitch, shows the ordered event timeline and displays detector metrics.
5. **Personalize** — casual, analyst and club modes change wording and emphasis while consuming the **same** factual payload.

This preserves the central product claim: personalization may change how a fact is explained, never the fact itself.

## Evidence interaction

For the synthetic high-press scenario the stream publishes pressure → failed pressured pass → explicit turnover → carry → pass → shot, followed by the `high_press` insight. Selecting that insight calls the existing evidence endpoint with its stable insight ID. The response contains the exact contributing event records and metrics, so a judge can move from an explanation back to source evidence.

The pitch does not interpolate player tracking, infer pressure geometry or invent intermediate positions. It renders only coordinates present in canonical synthetic events.

## DRY contracts

FastAPI response models are the transport source of truth. `scripts/export-openapi.py` writes the OpenAPI document and `openapi-typescript` generates `web/src/api/generated.ts`. Hand-written UI code imports those generated component schemas rather than duplicating backend DTO definitions.

The scenario registry also lives once in `pitchvolt.scenarios.SCENARIO_NAMES`; both scenario validation and the catalog endpoint use it.

CI regenerates OpenAPI and TypeScript contracts and fails if committed generated files drift. Frontend formatting, lint, type checking, tests and production build share one npm check command.

## Runtime boundary

Development keeps clear source boundaries: Uvicorn on port 8000 and Vite on port 5173, with Vite proxying `/api` to avoid development-only CORS configuration.

The production OCI image compiles React and copies the static bundle into the same runtime that serves FastAPI. FastAPI mounts that bundle only after explicit API routes. This gives the hackathon one deployable container, one origin for EventSource and evidence HTTP requests, and one Container Apps workload to cost-control. React and Python remain separate source modules and build stages; this packaging choice does not couple football logic to the UI.

Azure Container Apps and Microsoft Foundry are still **planned, not provisioned by this change**.

## Current limits

- Replays are short finite synthetic scenarios rather than a full match or licensed live feed.
- Audience wording is deterministic preview copy; it is not represented as AI-generated.
- The UI has no authentication or user persistence.
- EventSource resumes are supported by the API, but this first UI slice starts a fresh scenario when the replay controls change.
- Sustained possession remains a negative-control fixture and emits no tactical insight.

The fourth scenario, `statsbomb_high_press`, validates that StatsBomb-native synthetic pitch coordinates are normalized before UI delivery: the React pitch **always** receives canonical 105 × 68m event positions and never interprets 120 × 80 provider coordinates.


## Source-backed broadcast insight feed (October 2026)

The approved PitchVolt Application Preview is the only visual target. The Insights panel now
shows up to three **already published** tactical insights at the authoritative replay cursor,
newest first, using the existing `TacticalInsightPayload` and audience-specific deterministic
copy. It must not pad the panel with fabricated possession statistics, interpretations or
events. A disclosure preserves detailed metrics for the most recently published insight.
Selecting a row seeks to its recorded timestamp and requests its evidence using the existing
contract. Backward seeks hide later insights, narratives and evidence.

`sustained_possession` uses `sequence_duration_ms` and `passes`; it must never be described
using recovery-to-shot transition language. The 3D pitch may display the **single recorded event
actor**, at that original source coordinate, and explicitly labels the timestamp as *recorded*.
The actor is not a tracked player at intermediate times. Do not create 22-player positions,
invent a formation, invent a ball location, or interpolate between source events. Short
synthetic excerpts remain fictional; historical Open Data transport is outside this UI slice.
