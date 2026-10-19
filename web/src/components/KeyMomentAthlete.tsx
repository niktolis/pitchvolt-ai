import { useEffect, useMemo } from "react";
import * as THREE from "three";
import type { MatchEvent } from "../api/types";

/**
 * Explicitly ART-DIRECTED static illustration of a football action.
 * The source event authenticates only the player's ground position and event
 * category, NOT the posture, skeletal joints, face, uniform, or movement.
 */
export type EditorialPose = "neutral" | "stride" | "strike" | "defend";

export function editorialPoseForEvent(eventType: MatchEvent["event_type"]): EditorialPose {
  if (eventType === "shot" || eventType === "goal" || eventType === "pass") return "strike";
  if (eventType === "carry") return "stride";
  if (eventType === "pressure" || eventType === "tackle") return "defend";
  return "neutral";
}

function makeFabricBump(): THREE.CanvasTexture | null {
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const context = canvas.getContext("2d");
  if (!context) return null;
  // Original, reproducible woven material — no remote textures or imagery.
  context.fillStyle = "#808080";
  context.fillRect(0, 0, 128, 128);
  for (let row = 0; row < 128; row += 4) {
    for (let col = 0; col < 128; col += 4) {
      context.fillStyle = (row + col) % 8 ? "#9b9b9b" : "#626262";
      context.fillRect(col, row, 1.5, 2.5);
    }
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(3, 4);
  return texture;
}

/** Scene-local, medium-detail 3D human figure rendered only in Key Moment.
 * No real person's appearance, kit graphics, shirt number or pose is claimed.
 */
export function KeyMomentAthlete({
  kitColor,
  eventType,
}: {
  kitColor?: string;
  eventType: MatchEvent["event_type"];
}) {
  const pose = editorialPoseForEvent(eventType);
  const clothBump = useMemo(makeFabricBump, []);
  const materials = useMemo(() => {
    const shirt = new THREE.MeshPhysicalMaterial({
      color: kitColor ?? "#3aaee5",
      roughness: 0.58,
      metalness: 0.02,
      clearcoat: 0.12,
      clearcoatRoughness: 0.83,
      sheen: 0.45,
      sheenRoughness: 0.75,
      bumpMap: clothBump,
      bumpScale: 0.009,
    });
    return {
      shirt,
      trim: new THREE.MeshStandardMaterial({ color: "#e5f8eb", roughness: 0.79 }),
      shorts: new THREE.MeshStandardMaterial({ color: "#162b38", roughness: 0.76 }),
      skin: new THREE.MeshStandardMaterial({ color: "#b88462", roughness: 0.91 }),
      shadowSkin: new THREE.MeshStandardMaterial({ color: "#996444", roughness: 0.94 }),
      hair: new THREE.MeshStandardMaterial({ color: "#1b2222", roughness: 0.96 }),
      sock: new THREE.MeshStandardMaterial({ color: "#f1f5ea", roughness: 0.92 }),
      boot: new THREE.MeshPhysicalMaterial({
        color: "#10252b",
        roughness: 0.36,
        metalness: 0.02,
        clearcoat: 0.34,
      }),
      outsole: new THREE.MeshStandardMaterial({ color: "#d3f057", roughness: 0.83 }),
    };
  }, [clothBump, kitColor]);

  useEffect(
    () => () => {
      clothBump?.dispose();
      Object.values(materials).forEach((material) => material.dispose());
    },
    [clothBump, materials],
  );

  // Pose changes are art direction for an action CATEGORY, not source-tracked
  // joint samples or an animation of the player's recorded movement.
  const leftLeg = pose === "strike" ? 0.28 : pose === "stride" ? -0.25 : 0.04;
  const rightLeg = pose === "strike" ? -0.70 : pose === "stride" ? 0.35 : -0.04;
  const torsoLean = pose === "stride" ? 0.13 : pose === "defend" ? 0.18 : -0.07;
  const armSwing = pose === "stride" ? 0.3 : pose === "strike" ? 0.16 : 0.05;

  return (
    <group>
      {/* Everything is modeled in physical metres, feet at Y=0. */}
      <group position={[0, 1.03, 0]} rotation={[torsoLean, 0, 0]}>
        <mesh material={materials.shirt} castShadow receiveShadow position={[0, 0.28, 0]}>
          <capsuleGeometry args={[0.31, 0.31, 10, 24]} />
        </mesh>
        <mesh material={materials.shirt} castShadow position={[0, 0.48, 0]}>
          <sphereGeometry args={[0.37, 20, 18]} />
        </mesh>
        <mesh material={materials.shorts} castShadow position={[0, -0.06, 0]}>
          <cylinderGeometry args={[0.275, 0.30, 0.27, 20]} />
        </mesh>
        {/* Collar, sleeve piping and hand-authored football fabric folds. */}
        <mesh material={materials.trim} position={[0, 0.69, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.145, 0.027, 8, 24]} />
        </mesh>
        {[0.17, 0.31].map((height) => (
          <mesh key={height} material={materials.trim} position={[0, height, 0.303]}>
            <boxGeometry args={[0.48, 0.008, 0.008]} />
          </mesh>
        ))}
        <mesh material={materials.skin} castShadow position={[0, 0.78, 0]}>
          <cylinderGeometry args={[0.125, 0.132, 0.24, 20]} />
        </mesh>
        <mesh material={materials.skin} castShadow position={[0, 1.04, 0.01]}>
          <sphereGeometry args={[0.182, 28, 24]} />
        </mesh>
        <mesh material={materials.hair} castShadow position={[0, 1.13, -0.045]}>
          <sphereGeometry args={[0.18, 26, 18, 0, Math.PI * 2, 0, Math.PI * 0.51]} />
        </mesh>
        {/* Facial details visible in hero framing, neutral and non-identifying. */}
        {[-1, 1].map((side) => (
          <group key={side}>
            <mesh material={materials.shadowSkin} position={[side * 0.17, 1.04, 0]}>
              <sphereGeometry args={[0.04, 10, 10]} />
            </mesh>
            <mesh material={materials.hair} position={[side * 0.07, 1.065, 0.165]}>
              <sphereGeometry args={[0.017, 8, 8]} />
            </mesh>
            <group position={[side * 0.38, 0.45, 0]} rotation={[side * armSwing, 0, -side * 0.25]}>
              <mesh material={materials.shirt} castShadow position={[side * 0.035, -0.03, 0]}>
                <capsuleGeometry args={[0.142, 0.14, 8, 14]} />
              </mesh>
              <mesh material={materials.trim} position={[side * 0.045, -0.16, 0]}>
                <cylinderGeometry args={[0.14, 0.14, 0.027, 16]} />
              </mesh>
              <mesh material={materials.skin} castShadow position={[side * 0.07, -0.36, 0]}>
                <capsuleGeometry args={[0.091, 0.2, 8, 16]} />
              </mesh>
              <mesh material={materials.skin} castShadow position={[side * 0.07, -0.56, 0]}>
                <sphereGeometry args={[0.098, 12, 12]} />
              </mesh>
            </group>
          </group>
        ))}
      </group>
      {[-1, 1].map((side) => {
        const forward = side === -1 ? leftLeg : rightLeg;
        return (
          <group key={side} position={[side * 0.17, 0.99, 0]} rotation={[forward, 0, 0]}>
            <mesh material={materials.shorts} castShadow position={[0, -0.18, 0]}>
              <capsuleGeometry args={[0.16, 0.23, 8, 18]} />
            </mesh>
            <mesh material={materials.skin} castShadow position={[0, -0.44, 0]}>
              <sphereGeometry args={[0.125, 14, 14]} />
            </mesh>
            <mesh material={materials.sock} castShadow position={[0, -0.68, 0.008]}>
              <capsuleGeometry args={[0.118, 0.28, 8, 16]} />
            </mesh>
            <mesh material={materials.trim} position={[0, -0.51, 0.009]}>
              <cylinderGeometry args={[0.126, 0.125, 0.034, 18]} />
            </mesh>
            <mesh material={materials.boot} castShadow position={[0, -0.90, 0.135]}>
              <capsuleGeometry args={[0.15, 0.24, 8, 16]} />
            </mesh>
            <mesh material={materials.outsole} castShadow position={[0, -1.005, 0.148]}>
              <boxGeometry args={[0.29, 0.035, 0.38]} />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}
