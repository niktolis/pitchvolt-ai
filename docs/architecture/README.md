# MatchPulse AI — Software Architecture

This is the architectural entry point. **D2 source is authoritative**, while embedded SVGs are generated automatically to make the design readable in GitHub. The views explicitly distinguish *implemented* and *planned* behaviors.

## 1. Deployment view

![Deployment boundary and intended Azure integration](rendered/deployment.svg)

[Editable D2 source](diagrams/deployment.d2) · [Rendering and exports](rendering.md)

The current implementation runs locally as Python scenarios and a synchronous match processor. Azure Container Apps, Foundry, and React remain intended deployment components, **not implemented in this PR**. The deployment boundary clarifies who owns match state and where future streaming interfaces connect.

## 2. Dynamic sequence — From a football action to an overlay

![Event processing and planned narrative orchestration](rendered/streaming-sequence.svg)

[Editable D2 source](diagrams/streaming-sequence.d2)

The event source supplies a canonical event to the MatchProcessor. Each accepted event updates state and can emit a deterministic tactical insight with evidence IDs. The orchestrator/Foundry narrative calls and UI delivery are **planned**; their sequence conveys the approved two-speed architecture, not running functionality.

## 3. Tactical process / state flow

![Validation, possession change and tactical detection](rendered/tactical-state.svg)

[Editable D2 source](diagrams/tactical-state.d2)

Input validation precedes state mutation. A possession change requires an explicit turnover; otherwise the processor rejects the event. On a shot, the engine inspects a bounded causal window and may classify a pressing-assisted recovery or counterattack. [Business rules and worked examples](business-logic.md).

## 4. Maintenance contract

Every PR that changes architecture, behavior, or deployment must update relevant D2 sources **and** written explanation, regenerate checked SVGs, and keep all diagrams consistent with actual implementation. Validate rendering in the **Architecture diagrams** CI job and visually inspect the embedded Markdown images. No hand-maintained duplicate diagrams.

PDF and PPTX exports are produced as workflow artifacts; multi-board animations and clickable board navigation are available when future diagrams justify them. GitHub inline SVG embeds do not preserve interactive links, so this page provides ordinary links to each source and related documentation.
