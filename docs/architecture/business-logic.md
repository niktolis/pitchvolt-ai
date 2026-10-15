# Tactical intelligence — business logic

## Data and execution
The source is a fictional, seeded event scenario. Every action is converted to the canonical `MatchEvent` record with match ID, monotonically increasing sequence, match clock, possession owner, synthetic provenance and an event ID. The stateful `MatchProcessor.ingest` validates events before appending them. The pure `analyze_stream` function reuses exactly the same processor for replay/batch operation.

## Scenario: high press
At match minute 67 the home team presses, forcing an opponent's failed pass. The home team wins the ball through an explicit TURNOVER, advances through CARRY and PASS, and finishes with a SHOT. The detector identifies the opponent's failed pass marked `under_pressure`, the home PRESSURE event and subsequent attacking actions; it emits `high_press`, with evidence IDs and elapsed milliseconds from turnover to shot.

**Important:** `under_pressure` is supplied by the synthetic event source, not inferred from real tracking data. The detector currently proves consistency with the synthetic scenario, not independently verified tactical realism.

## Scenario: counterattack
Away team carries the ball; home team wins it through an explicit turnover, carries forward, passes and shoots. With no prior pressure+failed-pass combination, the detector emits `counterattack`.

## Scenario: sustained possession
Home team completes a number of passes and carries before a shot, never experiencing a turnover within the fixture. This is a **negative-control scenario** in this PR: no claim is emitted. A genuine sustained-possession detector with explicit threshold and time-window requirements will be implemented separately after review. Its absence is intentional and must not be advertised as implemented.

## Integrity checks
- Match/team ownership and contiguous event sequences.
- Monotonic period/clock and globally unique event IDs.
- Explicit TURNOVER required for possession-owner changes.
- Deterministic seed and fixture replay; repeatable evidence IDs.
- Invalid events rejected before mutation; no model API needed.

## Scope limitations
This is rule-based scenario detection, **not full real-world tracking or positional pressing analytics**. A PRESSURE event plus explicit `under_pressure` marker is a synthetic authoring convention. Detector bounded to eight recent events and 45 seconds. The current stream interface is synchronous and in-memory: future transports must preserve event ordering and replay offsets. A match-scoped processor is not safe to share as a mutable singleton across replicas; cloud scaling requires external state/event log.

## Architectural quality
DRY: one `MatchEvent` schema, one processor for streaming and batch. Provider adapters and agent prompts must not implement their own football statistics. Agent narratives read verified outputs, never own the source of truth.
