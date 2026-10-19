import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { inspectGLB } from "./hero-asset-audit.mjs";

const [original, optimized] = process.argv.slice(2);
if (!original || !optimized) throw new Error("Usage: node cc0-hero-inspect.mjs <original.glb> <optimized.glb>");

function inspect(path) {
  const bytes = readFileSync(path);
  if (bytes.toString("ascii", 0, 4) !== "glTF") throw new Error("Downloaded asset is not a GLB file");
  const length = bytes.readUInt32LE(12);
  if (length <= 0 || length > 2_000_000) throw new Error("Invalid GLB JSON length");
  const json = JSON.parse(bytes.toString("utf8", 20, 20 + length).trim());
  return {
    sha256: createHash("sha256").update(bytes).digest("hex"),
    bytes: bytes.length,
    materialNames: (json.materials ?? []).map((material) => material.name || "(unnamed)"),
    sceneNames: (json.scenes ?? []).map((scene) => scene.name || "(unnamed)"),
    meshCount: (json.meshes ?? []).length,
    vertices: (json.accessors ?? []).length,
    requiredExtensions: json.extensionsRequired ?? [],
  };
}
const source = inspect(original);
const target = inspect(optimized);
console.log("ORIGINAL_CC0_JSON=" + JSON.stringify(source));
console.log("OPTIMIZED_CC0_JSON=" + JSON.stringify(target));
try {
  console.log("VALIDATED_OPTIMIZED_MODEL=" + JSON.stringify(inspectGLB(readFileSync(optimized))));
} catch (error) {
  console.error("Optimized GLB does not yet meet production integration constraints: " + error.message);
  process.exitCode = 2;
}
