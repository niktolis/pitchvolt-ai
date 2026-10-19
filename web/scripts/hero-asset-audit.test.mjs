import { strict as assert } from "node:assert";
import { test } from "node:test";
import { inspectGLB, sha256 } from "./hero-asset-audit.mjs";

function makeGLB(gltf, binary = Buffer.alloc(4)) {
  const raw = Buffer.from(JSON.stringify(gltf), "utf8");
  const pad = (4 - (raw.length % 4)) % 4;
  const json = Buffer.concat([raw, Buffer.alloc(pad, 0x20)]);
  const body = Buffer.alloc(12 + 8 + json.length + 8 + binary.length);
  body.write("glTF", 0, "ascii");
  body.writeUInt32LE(2, 4);
  body.writeUInt32LE(body.length, 8);
  body.writeUInt32LE(json.length, 12);
  body.write("JSON", 16, "ascii");
  json.copy(body, 20);
  body.writeUInt32LE(binary.length, 20 + json.length);
  body.write("BIN\0", 24 + json.length, "ascii");
  binary.copy(body, 28 + json.length);
  return body;
}

const minimal = {
  asset: { version: "2.0" },
  meshes: [{ primitives: [{ attributes: { POSITION: 0 }, indices: 1 }] }],
  accessors: [{ count: 60 }, { count: 90 }],
  buffers: [{ byteLength: 4 }],
  materials: [{ name: "JerseyMaterial" }],
};

test("authored synthetic test-only GLB verifies triangle count and named jersey material", () => {
  const buffer = makeGLB(minimal);
  const metadata = inspectGLB(buffer);
  assert.deepEqual(metadata, {
    triangles: 30,
    materialNames: ["JerseyMaterial"],
    meshCount: 1,
  });
  assert.match(sha256(buffer), /^[0-9a-f]{64}$/);
});

test("rejects truncated and corrupted binary model headers", () => {
  assert.throws(() => inspectGLB(Buffer.from("glTF")), /Truncated/);
  const corrupt = makeGLB(minimal);
  corrupt.writeUInt32LE(3, 4);
  assert.throws(() => inspectGLB(corrupt), /glTF 2.0/);
  const wrongLength = makeGLB(minimal);
  wrongLength.writeUInt32LE(999, 8);
  assert.throws(() => inspectGLB(wrongLength), /declared length/);
});

test("external mesh and image URLs are never accepted", () => {
  for (const resource of [
    { images: [{ uri: "https://example.com/model.jpg" }] },
    { buffers: [{ uri: "../stolen.bin", byteLength: 10 }] },
  ]) {
    assert.throws(() => inspectGLB(makeGLB({ ...minimal, ...resource })), /external buffer or image/);
  }
});

test("rejects nontriangle meshes and over-budget models", () => {
  assert.throws(
    () => inspectGLB(makeGLB({ ...minimal, meshes: [{ primitives: [{ mode: 1, indices: 1 }] }] })),
    /Only triangle/,
  );
  assert.throws(
    () => inspectGLB(makeGLB({ ...minimal, accessors: [{ count: 60 }, { count: 400000 }] })),
    /triangle count budget/,
  );
});

test("refuses unidentifiable kit materials and malformed source metadata", () => {
  assert.throws(
    () => inspectGLB(makeGLB({ ...minimal, materials: [{ name: "" }] })),
    /material names absent/,
  );
});
