/**
 * A generic 3D football avatar, not an observed athlete mesh or measured pose.
 * Every position/heading is supplied by the source-linked event renderer.
 * Anatomical proportions and the football kit improve readability at the ROI camera scale.
 */
export function FootballActorAvatar({ kitColor }: { kitColor?: string }) {
  const jersey = kitColor ?? "#43aee7";

  return (
    <group>
      {/* Torso, with broad shoulders and a narrower waist. */}
      <mesh position={[0, 1.27, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.35, 0.27, 0.68, 14]} />
        <meshStandardMaterial color={jersey} roughness={0.72} />
      </mesh>
      <mesh position={[0, 1.01, 0]} castShadow>
        <cylinderGeometry args={[0.29, 0.32, 0.24, 12]} />
        <meshStandardMaterial color="#172e3d" roughness={0.82} />
      </mesh>
      <mesh position={[0, 1.59, 0]} castShadow>
        <cylinderGeometry args={[0.13, 0.17, 0.15, 12]} />
        <meshStandardMaterial color="#d8a77f" roughness={0.86} />
      </mesh>
      {/* A neutral football-shirt seam, not a sourced kit logo or shirt number. */}
      <mesh position={[0, 1.44, 0.303]} castShadow>
        <boxGeometry args={[0.49, 0.055, 0.024]} />
        <meshStandardMaterial color="#e5f3e7" roughness={0.82} />
      </mesh>

      {/* Head and hair, held in a neutral anatomical pose. */}
      <mesh position={[0, 1.76, 0]} castShadow>
        <sphereGeometry args={[0.183, 18, 16]} />
        <meshStandardMaterial color="#d8a77f" roughness={0.89} />
      </mesh>
      <mesh position={[0, 1.845, -0.025]} castShadow>
        <sphereGeometry args={[0.186, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.52]} />
        <meshStandardMaterial color="#252827" roughness={0.96} />
      </mesh>

      {[-1, 1].map((side) => (
        <group key={side}>
          {/* Short sleeves, forearms, hands. */}
          <mesh
            position={[side * 0.42, 1.40, 0]}
            rotation={[0, 0, -side * 0.2]}
            castShadow
          >
            <capsuleGeometry args={[0.16, 0.20, 4, 10]} />
            <meshStandardMaterial color={jersey} roughness={0.74} />
          </mesh>
          <mesh
            position={[side * 0.54, 1.12, 0]}
            rotation={[0, 0, -side * 0.23]}
            castShadow
          >
            <capsuleGeometry args={[0.105, 0.23, 4, 10]} />
            <meshStandardMaterial color="#d8a77f" roughness={0.88} />
          </mesh>
          <mesh position={[side * 0.59, 0.94, 0.015]} castShadow>
            <sphereGeometry args={[0.115, 10, 10]} />
            <meshStandardMaterial color="#d8a77f" roughness={0.89} />
          </mesh>

          {/* Separate thigh, knee, sock and boot geometry distinguishes a player from a marker. */}
          <mesh position={[side * 0.17, 0.79, 0]} castShadow>
            <capsuleGeometry args={[0.17, 0.29, 4, 10]} />
            <meshStandardMaterial color="#172e3d" roughness={0.9} />
          </mesh>
          <mesh position={[side * 0.17, 0.48, 0]} castShadow>
            <sphereGeometry args={[0.14, 10, 10]} />
            <meshStandardMaterial color="#d8a77f" roughness={0.9} />
          </mesh>
          <mesh position={[side * 0.17, 0.31, 0]} castShadow>
            <capsuleGeometry args={[0.125, 0.30, 4, 10]} />
            <meshStandardMaterial color="#e5f3e7" roughness={0.96} />
          </mesh>
          <mesh position={[side * 0.17, 0.105, 0.115]} castShadow>
            <boxGeometry args={[0.3, 0.17, 0.52]} />
            <meshStandardMaterial color="#172a2b" roughness={0.83} />
          </mesh>
          <mesh position={[side * 0.17, 0.187, 0.115]}>
            <boxGeometry args={[0.24, 0.022, 0.33]} />
            <meshStandardMaterial color="#b6e64b" roughness={0.88} />
          </mesh>
        </group>
      ))}
    </group>
  );
}
