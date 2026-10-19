import { readFileSync, writeFileSync } from "node:fs";
import { isRejectedHeroNodeName } from "./hero-asset-audit.mjs";

/**
 * Detach unobserved asset geometry from ALL glTF scene graphs at asset build
 * time, not just at runtime. Leaves unused binary buffer payload untouched;
 * the renderer has no path to instantiate the removed scene nodes.
 */
export function stripHeroProps(bytes) {
  if (!Buffer.isBuffer(bytes) || bytes.length < 28 || bytes.toString("ascii", 0, 4) !== "glTF") {
    throw new Error("Expected a GLB 2.0 binary");
  }
  if (bytes.readUInt32LE(4) !== 2 || bytes.readUInt32LE(8) !== bytes.length) {
    throw new Error("Invalid GLB version or length");
  }
  const jsonLength = bytes.readUInt32LE(12);
  if (jsonLength < 4 || jsonLength > 2_000_000 || 20 + jsonLength > bytes.length) {
    throw new Error("Invalid GLB metadata length");
  }
  if (bytes.toString("ascii", 16, 20) !== "JSON") throw new Error("Expected JSON chunk");
  const document = JSON.parse(bytes.toString("utf8", 20, 20 + jsonLength).trim());
  if (!Array.isArray(document.nodes) || !Array.isArray(document.scenes)) {
    throw new Error("Model requires explicit nodes and scenes");
  }
  const excluded = new Set();
  document.nodes.forEach((node, index) => {
    if (isRejectedHeroNodeName(node.name ?? "")) excluded.add(index);
  });
  if (!excluded.size) throw new Error("Expected known decorative ball/number props");
  for (const skin of document.skins ?? []) {
    if ((skin.joints ?? []).some((index) => excluded.has(index))) {
      throw new Error("Cannot remove a node used by a skeleton");
    }
  }
  for (const animation of document.animations ?? []) {
    if ((animation.channels ?? []).some((channel) => excluded.has(channel.target?.node))) {
      throw new Error("Cannot remove a node targeted by animation");
    }
  }
  const pruneLinks = (parent) => {
    if (Array.isArray(parent.nodes)) parent.nodes = parent.nodes.filter((index) => !excluded.has(index));
    if (Array.isArray(parent.children)) {
      parent.children = parent.children.filter((index) => !excluded.has(index));
    }
  };
  document.scenes.forEach(pruneLinks);
  document.nodes.forEach(pruneLinks);

  const json = Buffer.from(JSON.stringify(document), "utf8");
  const paddedLength = Math.ceil(json.length / 4) * 4;
  const rest = bytes.subarray(20 + jsonLength);
  const rebuilt = Buffer.alloc(20 + paddedLength + rest.length);
  rebuilt.write("glTF", 0, "ascii");
  rebuilt.writeUInt32LE(2, 4);
  rebuilt.writeUInt32LE(rebuilt.length, 8);
  rebuilt.writeUInt32LE(paddedLength, 12);
  rebuilt.write("JSON", 16, "ascii");
  json.copy(rebuilt, 20);
  rebuilt.fill(0x20, 20 + json.length, 20 + paddedLength);
  rest.copy(rebuilt, 20 + paddedLength);
  return { bytes: rebuilt, excluded: [...excluded].map((index) => document.nodes[index].name) };
}

if (process.argv[1]?.endsWith("/strip-hero-props.mjs")) {
  const [source, destination] = process.argv.slice(2);
  if (!source || !destination) throw new Error("Usage: strip-hero-props.mjs <input.glb> <output.glb>");
  const result = stripHeroProps(readFileSync(source));
  writeFileSync(destination, result.bytes);
  console.log(JSON.stringify({ output: destination, bytes: result.bytes.length, removedSceneNodes: result.excluded }));
}
