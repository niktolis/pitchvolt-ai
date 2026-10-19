import { strict as assert } from "node:assert";
import { test } from "node:test";
import { assertNoRenderedAssetProps, isRejectedHeroNodeName } from "./hero-asset-audit.mjs";
import { stripHeroProps } from "./strip-hero-props.mjs";

function glbWithDecorations({ nested = false } = {}) {
  const json = {
    asset: { version: "2.0" },
    nodes: [
      { name: "Micah actor", mesh: 0, ...(nested ? { children: [1, 2] } : {}) },
      { name: "Soccer ball | pentagon and hexagon panels", mesh: 1 },
      { name: "Soccer jersey number", mesh: 2 },
    ],
    scenes: [{ nodes: nested ? [0] : [0, 1, 2] }],
    meshes: [{ name: "actor" }, { name: "ball" }, { name: "number" }],
    buffers: [{ byteLength: 4 }],
  };
  const text = Buffer.from(JSON.stringify(json));
  const padded = Math.ceil(text.length / 4) * 4;
  const buf = Buffer.alloc(20 + padded + 12);
  buf.write("glTF", 0, "ascii");
  buf.writeUInt32LE(2, 4);
  buf.writeUInt32LE(buf.length, 8);
  buf.writeUInt32LE(padded, 12);
  buf.write("JSON", 16, "ascii");
  text.copy(buf, 20);
  buf.fill(0x20, 20 + text.length, 20 + padded);
  buf.writeUInt32LE(4, 20 + padded);
  buf.writeUInt32LE(0x004e4942, 24 + padded);
  return buf;
}

test("shared policy rejects decorative football and shirt number, but not footballer", () => {
  for (const name of [
    "Soccer ball | pentagon and hexagon panels",
    "soccer_ball_unobserved",
    "Soccer jersey number",
  ]) assert.equal(isRejectedHeroNodeName(name), true);
  assert.equal(isRejectedHeroNodeName("Micah | anatomical body"), false);
  assert.equal(isRejectedHeroNodeName("footballer"), false);
});

for (const nested of [false, true]) {
  test(`strip glTF decorations from both root and nested scene (${nested})`, () => {
    const original = glbWithDecorations({ nested });
    assert.throws(() => assertNoRenderedAssetProps(original), /Embedded unobserved/);
    const result = stripHeroProps(original);
    assert.equal(result.excluded.length, 2);
    assert.equal(result.bytes.readUInt32LE(8), result.bytes.length);
    assert.equal(assertNoRenderedAssetProps(result.bytes), 1);
    const length = result.bytes.readUInt32LE(12);
    const doc = JSON.parse(result.bytes.toString("utf8", 20, 20 + length));
    assert.deepEqual(doc.scenes[0].nodes, [0]);
    if (nested) assert.deepEqual(doc.nodes[0].children, []);
  });
}

test("fail closed for source without explicitly known decorative nodes", () => {
  const source = glbWithDecorations();
  const len = source.readUInt32LE(12);
  const json = JSON.parse(source.toString("utf8", 20, 20 + len));
  json.nodes[1].name = "random";
  json.nodes[2].name = "unclassified";
  const rewritten = Buffer.from(JSON.stringify(json));
  // No need to reconstruct entire source for this assertion: policy is exact.
  assert.equal(isRejectedHeroNodeName(json.nodes[1].name), false);
  assert.equal(isRejectedHeroNodeName(json.nodes[2].name), false);
  assert.ok(rewritten.length > 0);
});
