import { useThree } from "@react-three/fiber";
import { useLayoutEffect, useRef } from "react";
import * as THREE from "three";
import { toWorld, type PitchPoint } from "./pitch-geometry";

const BLADE_COUNT = 1400;

/**
 * Decorative stadium turf, independent of observed player/ball coordinates.
 * Deterministically batched into one instanced draw call for the close-up scene.
 */
export function KeyMomentGrass({ focus }: { focus: PitchPoint }) {
  const ref = useRef<THREE.InstancedMesh>(null);
  const invalidate = useThree((state) => state.invalidate);

  useLayoutEffect(() => {
    const mesh = ref.current;
    if (!mesh) return;
    const origin = toWorld(focus);
    const dummy = new THREE.Object3D();
    const dark = new THREE.Color("#294a20");
    const bright = new THREE.Color("#79a960");
    // Full deterministic hash; no Math.random() calls or animated positions.
    let state = 5192026;
    const random = () => {
      state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
      return state / 4294967296;
    };

    for (let i = 0; i < BLADE_COUNT; i += 1) {
      const radius = Math.sqrt(random()) * 9.5;
      const angle = random() * Math.PI * 2;
      const height = 0.07 + random() * 0.075;
      dummy.position.set(
        origin.x + radius * Math.cos(angle),
        height / 2,
        origin.z + radius * Math.sin(angle),
      );
      dummy.rotation.set((random() - 0.5) * 0.5, random() * Math.PI * 2, (random() - 0.5) * 0.35);
      dummy.scale.set(0.75 + random() * 0.7, height / 0.14, 0.65 + random() * 0.7);
      dummy.updateMatrix();
      mesh.setMatrixAt(i, dummy.matrix);
      mesh.setColorAt(i, dark.clone().lerp(bright, random()));
    }

    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    invalidate();
  }, [focus.x, focus.y, invalidate]);

  return (
    <instancedMesh ref={ref} args={[undefined, undefined, BLADE_COUNT]} frustumCulled={false}>
      <coneGeometry args={[0.017, 0.14, 3]} />
      <meshStandardMaterial
        color="#e1f2d7"
        roughness={0.94}
        side={THREE.DoubleSide}
      />
    </instancedMesh>
  );
}
