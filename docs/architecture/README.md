# MatchPulse AI software architecture

Architecture is documented as source and reviewed with each implementation PR. **D2 is authoritative** for diagrams. Keep the static deployment view, dynamic execution views, and narrative description consistent with the code.

- [Deployment architecture](diagrams/deployment.d2): Azure Container Apps deployment boundaries, current versus planned elements.
- [Stream processing sequence](diagrams/streaming-sequence.d2): event ingest, deterministic detectors, agent-based narratives, asynchronous overlay updates.
- [Tactical detection state transitions](diagrams/tactical-state.d2): simplified causal match-event flow and failure behavior.
- [Business logic and limitations](business-logic.md): scenarios, detection rules, tests, known gaps.

To render diagrams (if D2 is installed): `d2 docs/architecture/diagrams/deployment.d2 deployment.svg`. Similarly for other .d2 files. Editable .d2 files are the tracked source; generated SVGs are optional build artifacts.

**Architecture governance:** Every feature PR that alters components, data contracts, execution order, or deployment must update relevant diagrams and business logic, and document any consciously deferred capabilities. Do not create duplicate diagrams for identical concerns.
