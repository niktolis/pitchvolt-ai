import * as THREE from "three";

export const FIELD_WIDTH = 105;
export const FIELD_HEIGHT = 68;

// Tilted broadcast view, never a freehand correction to event coordinates.
export const BROADCAST_DIRECTION = new THREE.Vector3(0, 0.78, 0.625).normalize();

export type PitchPoint = { x: number; y: number };

/** Only event coordinates inside the canonical measured 105 × 68m pitch can be rendered. */
export function isSourcePitchPoint(point: PitchPoint | null | undefined): point is PitchPoint {
  return (
    point != null &&
    Number.isFinite(point.x) &&
    Number.isFinite(point.y) &&
    point.x >= 0 &&
    point.x <= FIELD_WIDTH &&
    point.y >= 0 &&
    point.y <= FIELD_HEIGHT
  );
}

export function toWorld(point: PitchPoint): THREE.Vector3 {
  return new THREE.Vector3(point.x - FIELD_WIDTH / 2, 0, point.y - FIELD_HEIGHT / 2);
}

/** Fit all four field corners inside the perspective-camera frustum. */
export function broadcastCameraPosition(
  aspect: number,
  verticalFovDegrees = 40,
  occupancy = 0.94,
): THREE.Vector3 {
  const tangent = Math.tan(THREE.MathUtils.degToRad(verticalFovDegrees / 2));
  const forward = BROADCAST_DIRECTION;
  const vertical = new THREE.Vector3(0, forward.z, -forward.y).normalize();
  const corners = [
    { x: 0, y: 0 },
    { x: FIELD_WIDTH, y: 0 },
    { x: FIELD_WIDTH, y: FIELD_HEIGHT },
    { x: 0, y: FIELD_HEIGHT },
  ];
  const distance = Math.max(
    ...corners.map((corner) => {
      const world = toWorld(corner);
      const depthOffset = world.dot(forward);
      const horizontalRequired = Math.abs(world.x) / (tangent * aspect * occupancy);
      const verticalRequired = Math.abs(world.dot(vertical)) / (tangent * occupancy);
      return depthOffset + Math.max(horizontalRequired, verticalRequired);
    }),
  );
  return forward.clone().multiplyScalar(distance + 3);
}

/**
 * A broadcast camera may pan between recorded actors without implying player tracking.
 * With a known source event, show a closer region of the pitch; when absent, show all.
 */
export function actionCameraPose(
  aspect: number,
  focus: PitchPoint | null | undefined,
): { position: THREE.Vector3; target: THREE.Vector3 } {
  const located = isSourcePitchPoint(focus);
  const fullFieldDistance = broadcastCameraPosition(aspect).length();
  const distance = fullFieldDistance * (located ? 0.58 : 1);
  if (!located) {
    return {
      position: BROADCAST_DIRECTION.clone().multiplyScalar(distance),
      target: new THREE.Vector3(),
    };
  }

  // Pan the *camera*, never observed player positions. Near a touchline,
  // avoid aiming directly beyond the field and exposing half an empty scene.
  // These margins reserve enough perspective space to keep a boundary actor visible.
  const tangent = Math.tan(THREE.MathUtils.degToRad(40 / 2));
  const horizontalInset = Math.min(FIELD_WIDTH / 2, distance * tangent * aspect * 0.7);
  const verticalInset = Math.min(
    FIELD_HEIGHT / 2,
    (distance * tangent * 0.7) / BROADCAST_DIRECTION.y,
  );
  const cameraFocus = {
    x: THREE.MathUtils.clamp(focus.x, horizontalInset, FIELD_WIDTH - horizontalInset),
    y: THREE.MathUtils.clamp(focus.y, verticalInset, FIELD_HEIGHT - verticalInset),
  };
  const target = toWorld(cameraFocus);
  return { position: target.clone().addScaledVector(BROADCAST_DIRECTION, distance), target };
}

/**
 * Cinematic but editorial close-up of an *observed event location*.
 * Moves the camera only; never supplies an athlete or ball trajectory.
 */
export function keyMomentCameraPose(
  focus: PitchPoint | null | undefined,
): { position: THREE.Vector3; target: THREE.Vector3 } | null {
  if (!isSourcePitchPoint(focus)) return null;
  const recorded = toWorld(focus);
  // Lower, longer-lens hero framing. Camera-only composition; the actor
  // stays at the exact source point and no tracking or gesture is inferred.
  const target = recorded.clone().add(new THREE.Vector3(0, 1.0, 0));
  return {
    position: target.clone().add(new THREE.Vector3(1.95, 1.55, 2.75)),
    target,
  };
}

/**
 * Position an on-screen player badge beside its source-linked avatar.
 * A right-sided source actor receives a left-extending badge and vice versa,
 * so the text does not cover the 3D body and stays inward at field boundaries.
 */
export function sourceActorBadgeAnchor(
  point: PitchPoint | null | undefined,
): { position: [number, number, number]; side: "left" | "right" } | null {
  if (!isSourcePitchPoint(point)) return null;
  const side = point.x > FIELD_WIDTH / 2 ? "left" : "right";
  return {
    position: [side === "left" ? -3 : 3, 2.72, 0],
    side,
  };
}

/** The source owns the destination. A missing shot endpoint is not invented. */
export function eventPath(
  source: PitchPoint,
  destination: PitchPoint | null | undefined,
): { start: THREE.Vector3; end: THREE.Vector3; length: number } | null {
  if (!isSourcePitchPoint(source) || !isSourcePitchPoint(destination)) return null;
  const start = toWorld(source);
  const end = toWorld(destination);
  const length = start.distanceTo(end);
  return length > 0.05 ? { start, end, length } : null;
}

/**
 * Deterministic geometry for a straight observed start to destination arrow.
 * The cone tip coincides with the recorded endpoint (not beyond it).
 * No path is rendered when the recorded destination is absent.
 */
export function sourceArrow(
  source: PitchPoint,
  destination: PitchPoint | null | undefined,
): {
  start: THREE.Vector3;
  end: THREE.Vector3;
  direction: THREE.Vector3;
  shaftCenter: THREE.Vector3;
  shaftLength: number;
  arrowCenter: THREE.Vector3;
  arrowLength: number;
} | null {
  const path = eventPath(source, destination);
  if (!path) return null;
  const direction = path.end.clone().sub(path.start).normalize();
  const arrowLength = Math.min(1.35, path.length * 0.3);
  const shaftLength = path.length - arrowLength;
  const shaftCenter = path.start.clone().addScaledVector(direction, shaftLength / 2);
  const arrowCenter = path.end.clone().addScaledVector(direction, -arrowLength / 2);
  return {
    start: path.start,
    end: path.end,
    direction,
    shaftCenter,
    shaftLength,
    arrowCenter,
    arrowLength,
  };
}

/** Orient the marker only when both recorded endpoints are valid; otherwise neutral. */
export function sourceActorHeading(
  location: PitchPoint,
  destination: PitchPoint | null | undefined,
): number {
  if (!isSourcePitchPoint(location) || !isSourcePitchPoint(destination)) return 0;
  if (location.x === destination.x && location.y === destination.y) return 0;
  return Math.atan2(destination.x - location.x, destination.y - location.y);
}
