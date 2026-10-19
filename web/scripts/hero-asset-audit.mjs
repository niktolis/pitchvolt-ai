import { createHash } from "node:crypto";
import { readFileSync, statSync } from "node:fs";
import { extname } from "node:path";

export const MAX_HERO_BYTES = 4 * 1024 * 1024;
export const MAX_HERO_TRIANGLES = 90000;

export function sha256(buffer) {
  return createHash("sha256").update(buffer).digest("hex");
}

/** No unverified network URI or unbounded GLB is eligible for rendering. */
export function inspectGLB(bytes) {
  if (!Buffer.isBuffer(bytes) || bytes.byteLength < 20) {
    throw new Error("Truncated GLB");
  }
  if (bytes.toString("ascii", 0, 4) !== "glTF" || bytes.readUInt32LE(4) !== 2) {
    throw new Error("Expected glTF 2.0 GLB magic and version");
  }
  if (bytes.readUInt32LE(8) !== bytes.byteLength) {
    throw new Error("GLB declared length must match actual bytes");
  }
  const jsonSize = bytes.readUInt32LE(12);
  if (!jsonSize || jsonSize > bytes.byteLength - 20 || jsonSize > 2_000_000) {
    throw new Error("Invalid GLB JSON chunk length");
  }
  if (bytes.toString("ascii", 16, 20) !== "JSON") {
    throw new Error("GLB must begin with a JSON chunk");
  }
  let gltf;
  try {
    gltf = JSON.parse(bytes.toString("utf8", 20, 20 + jsonSize).trim());
  } catch {
    throw new Error("GLB JSON is invalid");
  }
  if (gltf?.asset?.version !== "2.0" || !Array.isArray(gltf.meshes) || !gltf.meshes.length) {
    throw new Error("GLB needs glTF 2.0 asset metadata and at least one mesh");
  }
  // Unsupported compression must not trigger a hidden third-party decoder CDN.
  for (const name of gltf.extensionsRequired ?? []) {
    if (["KHR_draco_mesh_compression", "EXT_meshopt_compression", "KHR_texture_basisu"].includes(name)) {
      throw new Error("Model requires unsupported external decoder or texture codec");
    }
  }
  if (!Array.isArray(gltf.buffers) || !gltf.buffers.length) {
    throw new Error("A self-contained GLB binary buffer is mandatory");
  }
  const secondOffset = 20 + jsonSize;
  if (secondOffset + 8 > bytes.byteLength || bytes.readUInt32LE(secondOffset + 4) !== 0x004e4942) {
    throw new Error("GLB must contain embedded binary chunk");
  }
  // Self-hosted models must be self-contained and must not reference external resources.
  for (const resource of [...(gltf.buffers ?? []), ...(gltf.images ?? [])]) {
    if (resource.uri !== undefined) {
      throw new Error("GLB cannot include external buffer or image URIs");
    }
  }
  const triangles = gltf.meshes.reduce(
    (total, mesh) =>
      total +
      (mesh.primitives ?? []).reduce((subtotal, primitive) => {
        if (primitive.mode !== undefined && primitive.mode !== 4) {
          throw new Error("Only triangle mesh primitives are supported");
        }
        const accessorId = primitive.indices ?? primitive.attributes?.POSITION;
        const accessor = gltf.accessors?.[accessorId];
        if (!accessor || !Number.isInteger(accessor.count) || accessor.count < 3) {
          throw new Error("Mesh primitive needs a valid index or vertex accessor");
        }
        return subtotal + Math.floor(accessor.count / 3);
      }, 0),
    0,
  );
  if (!triangles || triangles > MAX_HERO_TRIANGLES) {
    throw new Error("Hero model exceeds triangle count budget");
  }
  const materialNames = (gltf.materials ?? []).map((material) => material.name).filter(Boolean);
  if (!materialNames.length) throw new Error("Cannot identify kit material; material names absent");
  return { triangles, materialNames, meshCount: gltf.meshes.length };
}

export function verifyHeroAsset(path, entry) {
  if (extname(path) !== ".glb" || !entry || typeof entry !== "object") {
    throw new Error("Expected a bundled GLB and an asset manifest entry");
  }
  const size = statSync(path).size;
  if (!size || size > MAX_HERO_BYTES) throw new Error("Hero model exceeds 4 MiB transfer budget");
  const bytes = readFileSync(path);
  if (!/^[0-9a-f]{64}$/.test(entry.sha256) || sha256(bytes) !== entry.sha256) {
    throw new Error("Hero model SHA-256 mismatch");
  }
  if (entry.bytes !== bytes.length) throw new Error("Hero model manifest byte count mismatch");
  if (!/^[0-9a-f]{64}$/.test(entry.sourceSha256)) {
    throw new Error("Source SHA-256 provenance is mandatory");
  }
  if (
    !entry.sourceUrl?.startsWith("https://www.innerscene.com/tools/library/3d-parts/") ||
    !/soccer-player-(standing|running|kicking)/.test(entry.sourceUrl)
  ) {
    throw new Error("Source asset URL is not in the reviewed CC0 soccer-player catalog");
  }
  if (entry.license !== "CC0-1.0") throw new Error("Asset must have verified CC0 status");
  if (entry.licenseUrl !== "https://www.innerscene.com/tools/library/terms") {
    throw new Error("Expected immutable documented terms reference");
  }
  const glb = inspectGLB(bytes);
  if (
    !entry.kitMaterial ||
    !glb.materialNames.includes(entry.kitMaterial) ||
    !Number.isFinite(entry.heightMetres) ||
    entry.heightMetres < 1.5 ||
    entry.heightMetres > 2.1
  ) {
    throw new Error("Explicit kit material and realistic asset height are mandatory");
  }
  return glb;
}
