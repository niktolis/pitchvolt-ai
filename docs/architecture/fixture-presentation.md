# Authored synthetic teams, score ledger and substitutions

PitchVolt's football truth remains the canonical `MatchEvent` stream. This
implementation adds **separate, explicit and validated fictional presentation
facts**. It never infers a starting lineup from a player's appearance,
substitution from changes in actor identity, or score from a shot or tactical
insight. No real historical club or individual is represented by these teams.

## Contract

`src/pitchvolt/presentation.py` owns the Pydantic schema and deterministic
fixture authoring:
- `TeamPresentation` gives a fictional team ID, name, abbreviation, distinct
  primary/secondary colors, text-only emblem label (not a licensed crest),
  authored coach name, exact roster/jersey numbers and optional explicit XI.
  Player surnames are **invented fixture-authoring data**, not extracted from
  jersey number strings, action coordinates or a historical dataset.
- `MatchPresentation` declares `coverage`, `initial_score_known`,
  `goals` as an **ordered score ledger**, and `substitutions` as separate
  explicitly authored source-fixture events. The lineup samples are
  authoritative **active-player ID** states after those events, not pitch
  coordinates.
- `extended_match` is an **authored fictional 0–0 kickoff fixture** and
  includes one explicit successful canonical GOAL. Other shots never change
  the scoreboard. Two **authored synthetic substitutions** at 61' and 65'
  reconcile subsequent canonical actor IDs, without adding fake spatial
  observations or changing the number of actions.
- Every short scenario is an excerpt in the second half. Its score is
  **unknown**, not zero; its starting XI is unavailable. Roster entries
  remain explicitly fictional but do not prove who started the match.
- The new read-only `GET /api/matches/{name}/presentation` route is
  synthetic-registry-only and does not alter existing `/timeline`,
  `/state`, `/stream`, `/evidence`, or narrative SSE contracts.

## Client cursor policy

The frontend chooses the **latest backend-authored score ledger entry at or
before the authoritative replay clock**; before any entry a known complete
fixture starts at an explicit 0–0. When `initial_score_known=false`, the
UI shows `– : –` rather than inventing a kickoff score. Active roster
snapshot selection follows the same cursor rule and source-issued authored
substitution timestamps. The backend alone validates goal/event and
substitution/roster causality; the browser must never infer score by scanning
unverified textual narratives. No source positions are invented.

## Future work

The existing `MatchEvent` union does not yet carry substitution events
or period boundary actions; this bundle's explicitly authored substitution
facts are typed **presentation source events** and are not merged into SSE
match-action history. Future source-neutral historical support requires a
versioned canonical substitution transport and verified licenses. The
text-only emblem is intentionally not a newly designed crest; original
fictional artwork and placement require approved design review.

All source JSON, token/Foundry behavior and paid Azure resources are unchanged.
