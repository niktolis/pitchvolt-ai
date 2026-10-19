# Licensed footballer GLB import pipeline — Issue #142

## Imported standing CC0 athlete — source-pinned integration, 19 October 2026

**Current feature branch** `feat/142-cc0-real-footballer` contains the
first **real third-party footballer mesh**, not just the GLB integration API.
This section supersedes the older empty-manifest descriptions below.

| Provenance / measured property | Value |
|---|---|
| Source | [Innerscene CC0 soccer player, standing](https://www.innerscene.com/tools/library/3d-parts/soccer-player-standing-3d-person-team-sports-f55b1b4f) |
| Source download | `https://www.innerscene.com/api/library/soccer-player-standing-3d-person-team-sports-f55b1b4f/download` |
| CC0 terms | `https://www.innerscene.com/tools/library/terms` |
| Original SHA-256 | `773cfa73bbcf659d7044934aaeacf1c3c9a49ae2955a51f56de7ad61ad1b6ffb` |
| Original size | 18,349,744 bytes |
| Optimized SHA-256 | `5bb8a63f2824d84c4f8a346ca11d6af0eefd1854050cfa3dde4fb12a134c6591` |
| Optimized size | **2,583,972 bytes (2.46 MiB)** |
| Triangles / meshes | **70,839 / 13** |
| Optimized model required extensions | `EXT_texture_webp`, `KHR_texture_transform` (both ordinary supported glTF/WebGL features; no meshopt/Draco decoder CDN) |
| Named recolorable material | `Micah | top` |
| Manifest | `web/src/assets/heroAssetManifest.json` |
| Embedded artifact | `web/public/assets/hero/neutral-5bb8a63f2824d84c.glb` |
| Production status | Only after explicit PR approval, merge and successful Azure deploy |

**Actual verified import procedure:** An isolated feature-branch GitHub
Actions runner downloaded the *official* CC0 binary, printed its SHA and
GLB material names, then verified the original SHA-256 on a subsequent
run. Pinned CLI:

```sh
npx --yes @gltf-transform/cli@4.5.1 optimize original.glb optimized.glb \
  --no-compress --texture-compress webp --texture-size 1024 \
  --simplify-ratio 0.65 --simplify-error 0.005
```

The optimized SHA was independently recorded and subsequently **checked
before import**. The existing `import-hero-asset.mjs` validated the original
hash, named jersey material, optimized GLB structure/mesh budget, expected
CC0 catalog origin, and generated the fingerprinted manifest. The
existing `check-hero-assets.mjs` and Node asset tests passed inside the
runner; the binary was committed to the **feature branch only**. The
temporary **write-privileged workflow was deleted after import** and does
not belong in the final application PR. See official job
https://github.com/niktolis/pitchvolt-ai/actions/runs/39255686666 .

**Identity, body pose and asset caveats:** This model is a static, textured,
anonymous footballer illustration; it has no real athlete identity,
observed joint tracking, runtime dribbling or source match footage. The
same **standing pose** is currently selected for all action event types
until separately verified standing/running/kicking models exist.
Recoloring `Micah | top` was authorized by its descriptive source
material name, not yet visually approved in-browser for both team
colors. The source player position/orientation and event-contact ball
marker rules are unchanged. Do not assume full AAA realism from merely
loading a static mesh. Require a screenshot at the exact deployed SHA
and check anatomy/feet, color/skin isolation, correct ground scale, camera
cropping, fallback and performance before accepting this upgrade.

---


**Status as of 19 October 2026:** Safe import path and fallback implemented.
**No binary third-party player asset is included in this PR**, and there is
no claim that the Key Moment already renders an external model. The
existing procedural player remains the production hero until a real
model is imported, visually approved and merged.

## Approved reference and rights

The binding visual reference is the PitchVolt Application Preview,
with manager-requested action ROI, cinematic close-up and EA FC-direction
character shading. **Do not copy EA Sports/FIFA/player likeness or
real-club trademarks.**

A first-party Innerscene catalog labels the following soccer players
**CC0 1.0** and attributes original MakeHuman CC0 assets:

| Pose | Catalog URL | Advertised original size |
|---|---|---|
| Standing / neutral | https://www.innerscene.com/tools/library/3d-parts/soccer-player-standing-3d-person-team-sports-f55b1b4f | 17.5 MB |
| Running / carry | https://www.innerscene.com/tools/library/3d-parts/soccer-player-running-3d-person-team-sports-7293f9db | 17.5 MB |
| Kicking / pass, shot | https://www.innerscene.com/tools/library/3d-parts/soccer-player-kicking-3d-person-team-sports-bc15ef89 | 17.5 MB |

The explicit terms at
https://www.innerscene.com/tools/library/terms
allow commercial redistribution/modification. This is **asset licensing
only**. Player positions, opponent locations, balls and match source
tracking remain independently controlled by Issue #134 and do not
follow from having a model. The catalog was inspected but the original
GLB download, embedded textures, geometry/material names, generated
SHA values and rendering compatibility were **not verified in the
assistant's runtime**.

## Mandatory import procedure

1. Obtain original GLB from its known official catalog entry.
   Confirm the source page, license and embedded materials/brand marks.
   Do not import unsolicited model/kit assets.
2. Independently compute `sha256sum original.glb`. Keep the original
   outside Git. **Never guess/pin a digest from the catalog filename**.
3. Optimize a **locally acquired** GLB with a pinned and reviewed tool:
   ```sh
   npx --yes @gltf-transform/cli@4.5.1 inspect original.glb
   npx --yes @gltf-transform/cli@4.5.1 optimize original.glb optimized.glb \
     --compress quantize --texture-compress webp --texture-size 1024 \
     --simplify-ratio 0.55 --simplify-error 0.001
   npx --yes @gltf-transform/cli@4.5.1 inspect optimized.glb
   ```
   Optimization must not introduce external texture URLs or runtime
   Draco/Meshopt decoder/CDN dependencies. Inspect exact material names
   and face/skin/kit separation. The user-approved branded color must
   only recolor a declared shirt-specific material.
4. Inspect the model in a browser *before publication* and verify
   ground-relative origin, 1.8m scale, football clothing and no
   unlicensed trademarks/real athlete identities.
5. Import exactly one tested optimized pose, specifying independently
   verified original SHA, confirmed jersey material and model height:
   ```sh
   cd web
   node scripts/import-hero-asset.mjs \
     --pose neutral \
     --source /private/original.glb \
     --source-sha256 <independently-verified-original-sha256> \
     --source-url https://www.innerscene.com/tools/library/3d-parts/soccer-player-standing-3d-person-team-sports-f55b1b4f \
     --optimized /private/optimized.glb \
     --kit-material <verified-shirt-material-name> \
     --height-metres 1.84
   npm run assets:check
   ```
   Repeat for `stride`, `strike` or `defend` only when the corresponding
   pose model is **actually available**, source verified and visually reviewed.
   If a specific category has no asset, the static fallback is used.
6. Review changes to `src/assets/heroAssetManifest.json` and
   `public/assets/hero/<pose>-<sha16>.glb` in a **separate PR**. The
   manifest records optimized file SHA-256, independent source SHA-256,
   upstream URL, declared CC0 license URL, size and jersey material.
   The model is served from the **application's own origin**, never
   from the vendor CDN. The file is loaded only when its manifest exists.
7. Require full CI, exact deployed SHA, realistic-appearance and
   low-power performance screenshots before final approval.

## Build and runtime invariants

- `npm run assets:check` is included in the production build. It
  verifies source/license metadata and manifest-to-file SHA-256 equality;
  rejects arbitrary URLs, external buffers/images, missing kit material,
  nontriangle meshes, more than **90,000 triangles**, and GLB payloads
  larger than **4 MiB per pose**. If optimization cannot meet budget
  without quality loss, review an explicit budget change separately.
- The default manifest is empty and triggers **zero network requests**.
  When a verified model exists, R3F loads it from the application
  origin; the existing procedural avatar renders during loading and
  on any GLB error. The 2D SVG path remains available without WebGL.
- A GLB's human pose is a **static editorial illustration**, never a
  source-observed joint/pose or interpolated match player. The
  `event.location` in the canonical 105×68m coordinate system
  controls the **only** actor world position.
- Do not mutate cached source model materials: model copies have their
  own shirt material, and own materials are disposed on unmount.
  Keep the secondary scene demand-rendered rather than a second
  continuously animated render loop.
- At the next visual acceptance check, verify the source action/ball
  contact, source surname/emblem, player no-cropping and color scheme
  across browser sizes before shipping other poses.

## Remaining constraints

The Innerscene models are about 112k triangles/17.5MB **before**
optimization. No compressed-byte size, correct jersey material name,
actual loader performance or visual fidelity can be claimed until the
real optimized binary has been checked. A static pose by itself also
cannot achieve EA FC-style gameplay animation. Truly moving players
and ball require separately verified, legally usable match tracking
(Issue #134).

### Model-embedded decorations filtered at runtime

Inspecting the original optimized GLB revealed meshes named
`Soccer ball | pentagon and hexagon panels` and `Soccer jersey number`.
These are illustration props, **not PitchVolt-sourced ball tracking or
shirt/athlete identity**. The `KeyMomentHero` scene explicitly hides
both through the tested `isUnobservedHeroProp` predicate, before
rendering any mesh. Only the separately timestamp-authorized
`RecordedBallContact` may draw an event-time marker, and only
source-authored player surname/emblem information is displayed.
Review actual render and source-action modes after deployment to
ensure bundled ball/number are absent even during pressure/turnover.
