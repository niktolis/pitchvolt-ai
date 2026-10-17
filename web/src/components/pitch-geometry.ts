import * as THREE from "three";

export const FIELD_WIDTH = 105;
export const FIELD_HEIGHT = 68;

// Tilted broadcast view, never a freehand correction to event coordinates.
export const BROADCAST_DIRECTION = new THREE.Vector3(0, 0.82, 0.57).normalize();

export type PitchPoint = { x: number; y: number };

export function toWorld(point: PitchPoint): THREE.Vector3 {
  return new THREE.Vector3(point.x - FIELD_WIDTH / 2, 0, point.y - FIELD_HEIGHT / 2);
}

/** Fit all four field corners inside the perspective-camera frustum. */
export function broadcastCameraPosition(
  aspect: number,
  verticalFovDegrees = 40,
  occupancy = 0.89,
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
  return forward.clone().multiplyScalar(distance + 4);
}

/** The source owns the destination. A missing shot endpoint is not invented. */
export function eventPath(
  source: PitchPoint,
  destination: PitchPoint | null | undefined,
): { start: THREE.Vector3; end: THREE.Vector3; length: number } | null {
  if (!destination) return null;
  const start = toWorld(source);
  const end = toWorld(destination);
  const length = start.distanceTo(end);
  return length > 0.05 ? { start, end, length } : null;
}
