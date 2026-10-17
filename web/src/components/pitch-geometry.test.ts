import { describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  broadcastCameraPosition,
  BROADCAST_DIRECTION,
  eventPath,
  toWorld,
} from "./pitch-geometry";

describe("source-aligned pitch camera", () => {
  it("maps canonical metres without changing recorded positions", () => {
    expect(toWorld({ x: 0, y: 0 }).toArray()).toEqual([-52.5, 0, -34]);
    expect(toWorld({ x: 105, y: 68 }).toArray()).toEqual([52.5, 0, 34]);
    expect(toWorld({ x: 52.5, y: 34 }).toArray()).toEqual([0, 0, 0]);
  });

  it.each([1.55, 1.75, 0.9])("frames every pitch corner for viewport aspect %s", (aspect) => {
    const camera = new THREE.PerspectiveCamera(40, aspect, 0.1, 420);
    camera.position.copy(broadcastCameraPosition(aspect));
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();

    for (const x of [0, 105]) {
      for (const y of [0, 68]) {
        const ndc = toWorld({ x, y }).project(camera);
        expect(Math.abs(ndc.x)).toBeLessThan(0.96);
        expect(Math.abs(ndc.y)).toBeLessThan(0.96);
        expect(ndc.z).toBeLessThan(1);
      }
    }
    expect(BROADCAST_DIRECTION.y).toBeGreaterThan(BROADCAST_DIRECTION.z);
  });

  it("does not synthesize a trajectory without a destination", () => {
    expect(eventPath({ x: 90, y: 20 }, null)).toBeNull();
    expect(eventPath({ x: 90, y: 20 }, { x: 90, y: 20 })).toBeNull();
    const result = eventPath({ x: 90, y: 20 }, { x: 96, y: 22 });
    expect(result?.length).toBeCloseTo(Math.hypot(6, 2));
    expect(result?.start.toArray()).toEqual([37.5, 0, -14]);
    expect(result?.end.toArray()).toEqual([43.5, 0, -12]);
  });
});
