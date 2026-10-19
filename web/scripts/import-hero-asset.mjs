import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { inspectGLB, MAX_HERO_BYTES, sha256 } from "./hero-asset-audit.mjs";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  const key = process.argv[i];
  const value = process.argv[i + 1];
  if (!key?.startsWith("--") || !value || value.startsWith("--")) {
    throw new Error("Expected --key value pairs");
  }
  args.set(key.slice(2), value);
}
const pose = args.get("pose");
if (!["neutral", "stride", "strike", "defend"].includes(pose)) throw new Error("Invalid editorial pose");
const sourceUrl = args.get("source-url");
const sourceSha256 = args.get("source-sha256");
const sourcePath = args.get("source");
const optimizedPath = args.get("optimized");
const kitMaterial = args.get("kit-material");
const heightMetres = Number(args.get("height-metres"));
if (
  !sourceUrl?.startsWith("https://www.innerscene.com/tools/library/3d-parts/") ||
  !/soccer-player-(standing|running|kicking)/.test(sourceUrl)
) throw new Error("Approved CC0 source URL required");
if (!sourcePath || !optimizedPath || !/^[0-9a-f]{64}$/.test(sourceSha256)) {
  throw new Error("An original source file and its independently verified SHA-256 are mandatory");
}
if (!kitMaterial || !Number.isFinite(heightMetres) || heightMetres < 1.5 || heightMetres > 2.1) {
  throw new Error("A validated shirt/jersey material name and stature are required");
}
const origin = readFileSync(sourcePath);
if (sha256(origin) !== sourceSha256) throw new Error("Original GLB provenance hash mismatch");
if (origin.length > 30 * 1024 * 1024) throw new Error("Unoptimized source exceeds safe acquisition bounds");
// Inspection before any copy prevents an arbitrary file from being imported.
const output = readFileSync(optimizedPath);
if (output.length > MAX_HERO_BYTES) throw new Error("Optimized GLB must be <= 4 MiB");
const inspected = inspectGLB(output);
if (!inspected.materialNames.includes(kitMaterial)) {
  throw new Error(`Kit material "${kitMaterial}" not found: ${inspected.materialNames.join(", ")}`);
}
const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const manifestPath = join(root, "src/assets/heroAssetManifest.json");
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const digest = sha256(output);
const path = join(root, "public/assets/hero");
mkdirSync(path, { recursive: true });
const fileName = `${pose}-${digest.slice(0, 16)}.glb`;
const storedPath = join(path, fileName);
if (!existsSync(storedPath)) copyFileSync(optimizedPath, storedPath);
manifest[pose] = {
  url: `/assets/hero/${fileName}`,
  sha256: digest,
  bytes: output.length,
  sourceSha256,
  sourceUrl,
  license: "CC0-1.0",
  licenseUrl: "https://www.innerscene.com/tools/library/terms",
  kitMaterial,
  heightMetres,
};
writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + "\n");
console.log(
  `Imported ${basename(storedPath)}: ${output.length} bytes, ${inspected.triangles} triangles. Review the resulting GLB visually before merging.`,
);
