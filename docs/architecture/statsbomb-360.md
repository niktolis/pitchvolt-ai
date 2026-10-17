# Source-backed StatsBomb 360 position snapshots

**Scope:** Offline ingestion and event alignment. No production historical
feed, hosted 360 API or fictional player tracking is enabled by this bundle.

StatsBomb Open Data provides `data/three-sixty/{match_id}.json` for **selected**
matches. The reference match 9880 used for action-frequency calibration has no
matching 360 file at the pinned upstream revision. Do not combine 360 from
another match with 9880 events or with the fictional `extended_match` scenario.

For a candidate 360-capable fixture, obtain *events*, *lineups*, and *three-sixty*
JSON from the **same pinned upstream revision**. Keep original files outside
Git and record independent SHA-256 values for each original asset.
The new loader reads an original `<match_id>.360.json` file, requires a
caller-supplied digest, validates each frame's `event_uuid` against the
separately verified event file, and normalizes its coordinates through the
existing provider adapter. It never downloads, modifies or redistributes
upstream data, and all CI tests run against explicitly constructed local data.

A 360 snapshot is *event-time*, not continuous positional tracking. It only
covers players visible to the camera; many events contain fewer than 22 players.
The flags `teammate`, `actor`, and `keeper` are source annotations.
Only the actor may be matched to the event's independently recorded player ID;
all other detections are **anonymous**. An observed full XI means exactly eleven
detections on each side within that single freeze frame, not that the dataset
provides persistent 22-player identities, movement paths, or a lineup.

When a frame is missing, the lookup returns **no frame** and consumers must
fall back to the current known event actor rather than reuse a previous/future
frame or reconstruct an illustrative 4-3-3. Never join by approximate time
alone, cross historical and synthetic match IDs, or interpolate missing data.

**Next integration boundary:** Promote these verified snapshots to a
versioned, opt-in historical replay transport; wire snapshots to the same
event-ID/cursor as pitch/timeline/evidence; render observed objects in both
WebGL and SVG. Keep historical inputs unavailable in the hosted demo until
redistribution and attribution requirements have been reviewed.

Upstream attribution: StatsBomb Open Data, Hudl,
https://github.com/hudl/open-data.
