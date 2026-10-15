# Synthetic events: first implementation slice

The MVP starts with one **fully original, fictional** causal sequence, seeded and replayable: high press → pressured pass failure → turnover → carry → progressive pass → shot.

Run locally after installing the project:

```shell
python -m pip install -e '.[dev]'
python -m pytest
python -c 'from matchpulse.simulation import high_press_replay; print([e.model_dump(mode="json") for e in high_press_replay()])'
```

The source adapter protocol and canonical event schema are in `src/matchpulse/events.py`. Coordinates use a normalized 105 × 68 metre pitch. Event times are simulated match-clock times, not live broadcast capture times.

**Deliberate limitations**: this is not yet a complete match simulator; it does not calculate tactical insights, player tracking speed, shot probabilities, or overlays. No StatsBomb records are imported. Before claiming football-realistic distributions, add explicit calibration and invariants and review reference licensing.

Acceptance for this slice: repeatability, schema-validation, ordered unique IDs, synthetically sourced records, and JSON roundtrips.
