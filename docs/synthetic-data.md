# Synthetic events: first implementation slice

The MVP starts with one **fully original, fictional** causal sequence, seeded and replayable: high press → pressured pass failure → turnover → carry → progressive pass → shot.

Run locally after installing the project:

```shell
python -m pip install -e '.[dev]'
python -m pytest
python -c 'from matchpulse.simulation import high_press_replay; print([e.model_dump(mode="json") for e in high_press_replay()])'
```

The source adapter protocol and canonical event schema are in `src/matchpulse/events.py`. Coordinates use a normalized 105 × 68 metre pitch. Event times are simulated match-clock times, not live broadcast capture times.

**Deliberate limitations**: this is not yet a complete match simulator or a general StatsBomb Open Data importer. It does not calculate player tracking speed or shot probabilities. No real StatsBomb records are imported. Before claiming football-realistic distributions, add explicit calibration and invariants and review reference licensing.

Acceptance for this slice: repeatability, schema-validation, ordered unique IDs, synthetically sourced records, and JSON roundtrips.


## StatsBomb-shaped fictional events (issue #15)

The canonical MatchPulse pitch remains **105 × 68 metres**; it is not a StatsBomb
120 × 80 coordinate pitch. The isolated adapter
`matchpulse.providers.statsbomb` maps **StatsBomb-native pitch coordinates**
to canonical metres, validates event type IDs, nested payloads, timestamps,
possession consistency, IDs and source provenance. These two conventions must
never be mixed inside `MatchProcessor` or React.

Generate original, **fictional** StatsBomb-shaped JSON using the already seeded
high-press scenario (no external data downloaded):

```python
import json
from matchpulse.scenarios import scenario
from matchpulse.providers.statsbomb import synthetic_to_statsbomb

match, events = scenario("high_press", seed=42)
print(json.dumps(synthetic_to_statsbomb(match, events), indent=2))
```

The generator emits fields used by the StatsBomb event JSON contract:
`id` (stable UUID), `index`, `period`, `timestamp`,
`minute`, `second`, `type` (numeric ID/name), `team`,
`player`, `possession`, `possession_team`, `location`, and nested
`pass`, `carry`, `shot` or `ball_recovery` when applicable.
Supported families for this **strict synthetic subset** are Pressure (17),
Pass (30), Ball Recovery (2), Carry (43) and Shot (16). A Shot with a
Goal outcome maps to canonical GOAL. A missing pass outcome is a completed pass;
Incomplete/Out/Pass Offside are failed passes.

The adapter deliberately represents a successful **Ball Recovery** as an
explicit canonical TURNOVER. A possession number increment alone is never
interpreted as a turnover. Same-team new possessions may therefore occur
without an invented turnover. Unsupported events, ambiguous outcomes, missing
locations/players, invalid team ownership, implicit possession-team changes and
failed ball recoveries are **rejected**, not silently skipped. This is not a
claim of support for complete real-match StatsBomb event streams.

Replay through the existing public API and React interface:

```sh
curl http://localhost:8000/api/scenarios
curl http://localhost:8000/api/matches/statsbomb_high_press/state
curl -N 'http://localhost:8000/api/matches/statsbomb_high_press/stream?speed=1000'
```

`statsbomb_high_press` is generated from a separate, identifiable
StatsBomb-shaped synthetic provider path; the resulting canonical events
pass through the **same** `MatchProcessor`, evidence endpoint, SSE and React
UI as `high_press`. Their tactical kind and deterministic metrics agree.

**Provenance / licensing:** The output is original fiction shaped like the
StatsBomb schema, *not* actual open-match data. Data in
https://github.com/hudl/open-data are historical real events and must **never**
be relabeled synthetic. The Open Data repo requests source and logo attribution
on public analysis; redistribution/commercial terms need separate review.
Full historical-data import, broader event families, 3rd/4th periods,
unstructured match metadata, 3D shot-height data (deliberately not fabricated), frame/360 support, and production-scale event
semantics remain tracked in [issue #15](https://github.com/niktolis/matchpulse-ai/issues/15).


## New primary acceptance direction (October 2026)

Long-form replay and data-source interoperability become the main testing baseline. See [StatsBomb-based replay baseline](statsbomb-baseline.md) for separate real Open Data ingestion and seeded original synthetic match generation, provenance/attribution policy and acceptance gates. The existing short scenarios remain regression tests.
