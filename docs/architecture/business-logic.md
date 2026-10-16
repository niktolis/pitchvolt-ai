# Tactical intelligence — business logic

## Data and execution

The source is a fictional, seeded event scenario. Every action is converted to the canonical `MatchEvent` record with match ID, monotonically increasing sequence, match clock, possession owner, synthetic provenance and an event ID. The stateful `MatchProcessor.ingest` validates events before appending them. The pure `analyze_stream` function reuses exactly the same processor for replay/batch operation.

FastAPI and React are adapters around this logic. Neither transport nor presentation owns tactical calculations.

## Scenario: high press

At match minute 67 the home team presses, forcing an opponent's failed pass. The home team wins the ball through an explicit TURNOVER, advances through CARRY and PASS, and finishes with a SHOT. The detector identifies the opponent's failed pass marked `under_pressure`, the home PRESSURE event and subsequent attacking actions; it emits `high_press`, with evidence IDs and elapsed milliseconds from turnover to shot.

**Important:** `under_pressure` is supplied by the synthetic event source, not inferred from real tracking data. The detector currently proves consistency with the synthetic scenario, not independently verified tactical realism.

### Concrete publication example

For the high-press fixture, the SSE fast path emits the six canonical actions in order and then the tactical insight immediately after the triggering shot. The insight contains:

- a stable insight ID derived from the shot event;
- the recovering/attacking team;
- exact source event IDs;
- `transition_duration_ms`;
- `attacking_actions`.

The React client renders those fields directly. Casual, analyst and club modes derive wording from the same payload; they never recompute the metric.

## Scenario: counterattack

Away team carries the ball; home team wins it through an explicit turnover, carries forward, passes and shoots. With no prior pressure + failed pressured-pass combination, the detector emits `counterattack`.

## Scenario: sustained possession

Home team completes several passes and carries before a shot, never experiencing a turnover within the fixture. This is a **negative-control scenario**: no tactical claim is emitted. A genuine sustained-possession detector requires an explicit reviewed threshold/window before it can be advertised as implemented.

## Integrity checks

- Match/team ownership and contiguous event sequences.
- Monotonic period/clock and globally unique event IDs.
- Explicit TURNOVER required for possession-owner changes.
- A turnover must award possession to the recovering team.
- Deterministic seed and fixture replay; repeatable evidence IDs.
- Invalid events are rejected before state mutation.
- Batch analysis and incremental streaming use the same `MatchProcessor`.
- No model API is needed to calculate football facts.

## Scope limitations

This is rule-based scenario detection, **not full real-world tracking or positional pressing analytics**. A PRESSURE event plus explicit `under_pressure` marker is a synthetic authoring convention. The detector is bounded to eight recent events and 45 seconds.

The current transport is a finite, stateless synthetic SSE replay. Every subscriber reconstructs an immutable scenario and can resume from a deterministic publication cursor. This avoids shared mutable server state for the MVP, but it is not a persisted live-feed architecture. A future dynamic multi-replica feed requires an external ordered event log/state store and idempotent checkpoints before horizontal scaling.

## Architectural quality

DRY is a correctness mechanism:

- one canonical `MatchEvent` schema;
- one `MatchProcessor` for incremental and batch analysis;
- one scenario registry;
- one insight-to-transport mapping;
- FastAPI OpenAPI as the generated TypeScript contract source;
- one immutable factual payload across audience modes.

Provider adapters, agent prompts and UI code must not implement independent football statistics. Future agent narratives read verified outputs and must pass deterministic claim verification before publication.

## StatsBomb-shaped synthetic source — same deterministic truth

The `statsbomb_high_press` fixture deliberately serializes **fictional** high-press actions into StatsBomb-style JSON (Pressure → Pass / Incomplete → Ball Recovery → Carry → Pass → Shot) and ingests them back through the strict provider adapter. For example, a source location `[80, 40]` maps to canonical `(70, 34)` metres. Ball Recovery is mapped to explicit TURNOVER only if it succeeds and awards possession to its recovering team; a new StatsBomb possession ID alone never fabricates a turnover. Both native and adapted fixtures publish `high_press` and the same transition duration/action-count metrics from **one** detector; source evidence IDs differ because the adapter uses stable StatsBomb-shaped UUIDs. Unsupported provider events fail rather than silently biasing metrics. See [synthetic provider contract](../synthetic-data.md) and [issue #15](https://github.com/niktolis/matchpulse-ai/issues/15).
