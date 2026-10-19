import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { verifyHeroAsset } from "./hero-asset-audit.mjs";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const entries = JSON.parse(readFileSync(join(root, "src/assets/heroAssetManifest.json"), "utf8"));
if (!entries || typeof entries !== "object" || Array.isArray(entries)) {
  throw new Error("Hero asset manifest must be an object");
}
for (const [kind, value] of Object.entries(entries)) {
  if (!["neutral", "stride", "strike", "defend"].includes(kind)) {
    throw new Error(`Unknown hero pose: ${kind}`);
  }
  if (!value || typeof value !== "object" || !/^\/assets\/hero\/[a-z-]+-[a-f0-9]{16}\.glb$/.test(value.url)) {
    throw new Error("Hero URL must be fingerprinted and self-hosted");
  }
  const file = join(root, "public", value.url.slice(1));
  const info = verifyHeroAsset(file, value);
  console.log(`Verified ${kind}: ${info.triangles} triangles, ${value.bytes} bytes`);
}
console.log(`Verified ${Object.keys(entries).length} self-hosted hero assets; procedural fallback stays available.`);
