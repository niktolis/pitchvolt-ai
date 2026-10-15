# Real-time match API — business behavior and constraints

## User-visible behavior

The match engine detects facts independently of the LLM. For example, a fictional Harbor FC pressure event and a failed pressured Ridge FC pass are followed by an explicit turnover, attacking pass and shot. The processor emits a high-press insight with the contributing event IDs. Clients receive six canonical events and one insight as individually ordered **Server-Sent Events**.

The SSE envelope has a numeric `id`, an `event` name (`match_event` or `tactical_insight`), and JSON `data`. The insight is published immediately after the triggering shot. `event: replay_complete` terminates the finite scenario stream; future real feeds will be long-lived.

## HTTP endpoints

- `GET /health`: process readiness probe (currently simple process health).
- `GET /api/scenarios`: supported synthetic scenarios.
- `GET /api/matches/{name}/state`: deterministic full-fixture match state and insights (not a live mutable cursor).
- `GET /api/matches/{name}/evidence/{insight_id}`: immutable evidence records for one insight; future read-only agent tool.
- `GET /api/matches/{name}/stream?speed=1&after=0`: finite replay using `speed` (0.1–1000×) and optional numeric `after` cursor. `Last-Event-ID` takes precedence when reconnecting.

For local demo: `curl -N 'http://localhost:8000/api/matches/high_press/stream?speed=1000'`. Browser `EventSource` also works on the same origin.

## Streaming design

Each subscriber constructs an independent `MatchProcessor`; it replays one deterministic fixture and emits a single `timeline()` publication contract. No global mutable state, background worker, or model calls are required. Reconnects use the deterministic message ID, not a mutable server buffer. The source clock determines the sleep between frames. `speed` changes replay wall-clock delay only, never match timing or football facts.

The fast path is **implemented as a finite synthetic SSE replay** and is consumed by the React live-broadcast UI. The asynchronous Foundry narrative path, multi-match state store, persistence, access control, persisted user preferences, and live external feed connectors are **not implemented**.

## Limitations and operational consequences

- This is a functional transport MVP, not a production live match feed.
- `state` returns the completed fixture; it does not follow a viewer's individual playback cursor. UI should build its live state from the SSE events.
- Every connection reconstructs a short fixture; extended matches will need caching/ordered event logs for efficiency.
- `after` and `Last-Event-ID` refer to **published message IDs** (events plus insights), not just football event sequence numbers.
- No cross-replica state consistency problem yet, because streams are reconstructed from fixed immutable fixtures. Dynamic live feeds will need persisted ordering and recoverable checkpoints.
- Disconnections do not mutate shared state. A reconnection can resume the exact deterministic stream, but accumulated *live* realtime events are not persisted.
- Agent inference must never block SSE publication. Future narratives must reference the same insight ID and evidence; the current UI already reserves that factual boundary.
- No claims of measured p95 latency or concurrent-user scaling yet.

## Architecture ownership

`src/matchpulse/api.py` is an adapter. Football validation/detection stays in `MatchProcessor`. Stream and evidence endpoints reference the existing canonical schema and deterministic insight calculations. Do not duplicate football statistics or embed LLM calls in the transport.

## Additional synthetic input path

`statsbomb_high_press` is a fourth supported synthetic scenario, produced by the StatsBomb-shaped fixture generator and provider adapter. Existing `/api/scenarios`, `state`, `timeline`, `stream` and `evidence` APIs require **no** special-case transport branch because they consume the canonical model. The API does not yet accept arbitrary uploaded StatsBomb files or provide live external feeds; full integration is tracked in #15.
