import * as THREE from "three";
import { describe, expect, it } from "vitest";
import {
  BROADCAST_DIRECTION,
  broadcastCameraPosition,
  eventPath,
  isSourcePitchPoint,
  sourceArrow,
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
        const head = toWorld({ x, y })
          .add(new THREE.Vector3(0, 2.8, 0))
          .project(camera);
        expect(Math.abs(head.x)).toBeLessThan(1);
        expect(Math.abs(head.y)).toBeLessThan(1);
        expect(head.z).toBeLessThan(1);
      }
    }
    expect(BROADCAST_DIRECTION.y).toBeGreaterThan(BROADCAST_DIRECTION.z);
  });

  it("renders only finite positions inside the canonical source coordinate system", () => {
    expect(isSourcePitchPoint({ x: 0, y: 0 })).toBe(true);
    expect(isSourcePitchPoint({ x: 105, y: 68 })).toBe(true);
    expect(isSourcePitchPoint({ x: 105.01, y: 34 })).toBe(false);
    expect(isSourcePitchPoint({ x: -1, y: 34 })).toBe(false);
    expect(isSourcePitchPoint({ x: 10, y: Number.NaN })).toBe(false);
    expect(isSourcePitchPoint({ x: Number.POSITIVE_INFINITY, y: 20 })).toBe(false);
    expect(isSourcePitchPoint(null)).toBe(false);
  });

  it("keeps the entire arrow inside its recorded start and end positions", () => {
    const source = { x: 63, y: 27 };
    const destination = { x: 92, y: 31 };
    const arrow = sourceArrow(source, destination);
    expect(arrow).not.toBeNull();
    if (!arrow) return;
    expect(arrow.start.toArray()).toEqual(toWorld(source).toArray());
    expect(arrow.end.toArray()).toEqual(toWorld(destination).toArray());
    const tip = arrow.arrowCenter.clone().addScaledVector(arrow.direction, arrow.arrowLength / 2);
    const shaftEnd = arrow.shaftCenter
      .clone()
      .addScaledVector(arrow.direction, arrow.shaftLength / 2);
    const headStart = arrow.arrowCenter
      .clone()
      .addScaledVector(arrow.direction, -arrow.arrowLength / 2);
    expect(tip.distanceTo(arrow.end)).toBeLessThan(1e-6);
    expect(shaftEnd.distanceTo(headStart)).toBeLessThan(1e-6);
    expect(arrow.shaftLength + arrow.arrowLength).toBeCloseTo(arrow.start.distanceTo(arrow.end));
  });

  it("does not synthesize a trajectory without a destination", () => {
    expect(eventPath({ x: 90, y: 20 }, null)).toBeNull();
    expect(sourceArrow({ x: 90, y: 20 }, null)).toBeNull();
    expect(sourceArrow({ x: 95, y: 20 }, { x: 999, y: 20 })).toBeNull();
    expect(eventPath({ x: 90, y: 20 }, { x: 90, y: 20 })).toBeNull();
    const result = eventPath({ x: 90, y: 20 }, { x: 96, y: 22 });
    expect(result?.length).toBeCloseTo(Math.hypot(6, 2));
    expect(result?.start.toArray()).toEqual([37.5, 0, -14]);
    expect(result?.end.toArray()).toEqual([43.5, 0, -12]);
  });
});
