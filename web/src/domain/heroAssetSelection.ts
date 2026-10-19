import type { MatchEvent } from "../api/types";
import manifest from "../assets/heroAssetManifest.json";
import { type EditorialPose, editorialPoseForEvent } from "../components/KeyMomentAthlete";

export interface VerifiedHeroAsset {
  url: string;
  sha256: string;
  bytes: number;
  sourceSha256: string;
  sourceUrl: string;
  license: "CC0-1.0";
  licenseUrl: string;
  kitMaterial: string;
  heightMetres: number;
}
const modelAssets = manifest as Partial<Record<EditorialPose, VerifiedHeroAsset>>;

/** Never load an external GLB, and prefer the original procedural fallback. */
export function heroAssetForEvent(eventType: MatchEvent["event_type"]): VerifiedHeroAsset | null {
  const pose = editorialPoseForEvent(eventType);
  const asset = modelAssets[pose] ?? modelAssets.neutral;
  if (
    !asset ||
    !/^\/assets\/hero\/[a-z-]+-[a-f0-9]{16}\.glb$/.test(asset.url) ||
    asset.license !== "CC0-1.0"
  ) {
    return null;
  }
  return asset;
}
