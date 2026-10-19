import * as THREE from "three";
import { describe, expect, it } from "vitest";
import {
  actionCameraPose,
  BROADCAST_DIRECTION,
  broadcastCameraPosition,
  eventPath,
  isSourcePitchPoint,
  keyMomentCameraPose,
  sourceActorBadgeAnchor,
  sourceActorHeading,
  sourceArrow,
  toWorld,
} from "./pitch-geometry";

describe("source-aligned pitch camera", () => {
  it("maps canonical metres without changing recorded positions", () => {
    expect(toWorld({ x: 0, y: 0 }).toArray()).toEqual([-52.5, 0, -34]);
    expect(toWorld({ x: 105, y: 68 }).toArray()).toEqual([52.5, 0, 34]);
    expect(toWorld({ x: 52.5, y: 34 }).toArray()).toEqual([0, 0, 0]);
  });

  it.each([0.75, 1.55, 2.1])(
    "frames a close-up of only the recorded actor, including pitch boundaries at aspect %s",
    (aspect) => {
      for (const point of [
        { x: 0, y: 0 },
        { x: 52.5, y: 34 },
        { x: 105, y: 68 },
      ]) {
        const pose = keyMomentCameraPose(point);
        expect(pose).not.toBeNull();
        if (!pose) return;
        const world = toWorld(point);
        expect(pose.target.x).toBe(world.x);
        expect(pose.target.z).toBe(world.z);
        expect(pose.position.distanceTo(pose.target)).toBeLessThan(8);
        const camera = new THREE.PerspectiveCamera(38, aspect, 0.1, 160);
        camera.position.copy(pose.position);
        camera.lookAt(pose.target);
        camera.updateProjectionMatrix();
        camera.updateMatrixWorld();
        const head = world
          .clone()
          .add(new THREE.Vector3(0, 1.8, 0))
          .project(camera);
        expect(Math.abs(head.x)).toBeLessThan(0.7);
        expect(Math.abs(head.y)).toBeLessThan(0.7);
        expect(head.z).toBeGreaterThan(-1);
        expect(head.z).toBeLessThan(1);
      }
    },
  );

  it("refuses a fabricated Key Moment location when no valid event exists", () => {
    expect(keyMomentCameraPose(null)).toBeNull();
    expect(keyMomentCameraPose({ x: Number.NaN, y: 8 })).toBeNull();
    expect(keyMomentCameraPose({ x: 110, y: 30 })).toBeNull();
    expect(keyMomentCameraPose({ x: -2, y: 22 })).toBeNull();
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

  it.each([1.55, 1.75, 0.9])(
    "focuses the recorded action without showing the whole field at aspect %s",
    (aspect) => {
      const focus = { x: 91, y: 15 };
      const pose = actionCameraPose(aspect, focus);
      const camera = new THREE.PerspectiveCamera(40, aspect, 0.1, 420);
      camera.position.copy(pose.position);
      camera.lookAt(pose.target);
      camera.updateProjectionMatrix();
      camera.updateMatrixWorld();

      const actor = toWorld(focus).project(camera);
      expect(Math.abs(actor.x)).toBeLessThan(0.95);
      expect(Math.abs(actor.y)).toBeLessThan(0.95);
      const corners = [
        { x: 0, y: 0 },
        { x: 105, y: 0 },
        { x: 105, y: 68 },
        { x: 0, y: 68 },
      ];
      expect(
        corners.some((corner) => {
          const projected = toWorld(corner).project(camera);
          return Math.abs(projected.x) > 1 || Math.abs(projected.y) > 1;
        }),
      ).toBe(true);
      expect(pose.position.distanceTo(pose.target)).toBeLessThan(
        broadcastCameraPosition(aspect).length() * 0.7,
      );
    },
  );

  it.each([0.9, 1.55, 1.75])(
    "keeps recorded touchline and goal-line actors visible at aspect %s",
    (aspect) => {
      for (const focus of [
        { x: 0, y: 0 },
        { x: 0, y: 68 },
        { x: 105, y: 0 },
        { x: 105, y: 68 },
      ]) {
        const pose = actionCameraPose(aspect, focus);
        const camera = new THREE.PerspectiveCamera(40, aspect, 0.1, 420);
        camera.position.copy(pose.position);
        camera.lookAt(pose.target);
        camera.updateProjectionMatrix();
        camera.updateMatrixWorld();
        const actor = toWorld(focus).project(camera);
        expect(Math.abs(actor.x)).toBeLessThan(0.95);
        expect(Math.abs(actor.y)).toBeLessThan(0.95);
        expect(pose.target.toArray()).not.toEqual(toWorld(focus).toArray());
      }
    },
  );

  it("keeps the entire field as a fallback when action coordinates are absent or invalid", () => {
    const fallback = broadcastCameraPosition(1.55);
    for (const focus of [null, { x: 999, y: 10 }, { x: Number.NaN, y: 30 }]) {
      const pose = actionCameraPose(1.55, focus);
      expect(pose.position.toArray()).toEqual(fallback.toArray());
      expect(pose.target.toArray()).toEqual([0, 0, 0]);
    }
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

  it("never orients a source actor toward invalid or absent destinations", () => {
    const location = { x: 40, y: 20 };
    expect(sourceActorHeading(location, { x: 50, y: 20 })).toBeCloseTo(Math.PI / 2);
    expect(sourceActorHeading(location, { x: 40, y: 30 })).toBe(0);
    expect(sourceActorHeading(location, { x: 1000, y: 20 })).toBe(0);
    expect(sourceActorHeading(location, { x: Number.NaN, y: 20 })).toBe(0);
    expect(sourceActorHeading(location, null)).toBe(0);
    expect(sourceActorHeading(location, location)).toBe(0);
  });

  it("keeps source-linked surname/crest badges offset inward from every field edge", () => {
    expect(sourceActorBadgeAnchor({ x: 0, y: 0 })).toEqual({
      position: [3, 2.72, 0],
      side: "right",
    });
    expect(sourceActorBadgeAnchor({ x: 105, y: 68 })).toEqual({
      position: [-3, 2.72, 0],
      side: "left",
    });
    expect(sourceActorBadgeAnchor({ x: 52.5, y: 34 })?.side).toBe("right");
    expect(sourceActorBadgeAnchor({ x: 52.51, y: 34 })?.side).toBe("left");
    for (const x of [0, 12, 52.5, 78, 105]) {
      const badge = sourceActorBadgeAnchor({ x, y: 30 });
      expect(badge).not.toBeNull();
      if (!badge) continue;
      expect(x + badge.position[0]).toBeGreaterThan(0);
      expect(x + badge.position[0]).toBeLessThan(105);
      expect(Math.abs(badge.position[0])).toBeGreaterThan(2.5);
    }
  });

  it("never displays actor metadata at an invalid or missing source position", () => {
    expect(sourceActorBadgeAnchor({ x: -1, y: 30 })).toBeNull();
    expect(sourceActorBadgeAnchor({ x: 53, y: 70 })).toBeNull();
    expect(sourceActorBadgeAnchor({ x: Number.NaN, y: 30 })).toBeNull();
    expect(sourceActorBadgeAnchor(null)).toBeNull();
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
