import { Canvas } from "@react-three/fiber";
import { useMemo } from "react";
import * as THREE from "three";
import type { MatchEvent } from "../api/types";

type Point = { x: number; y: number };

export function pitchWorld(point: Point): [number, number, number] {
  return [point.x - 52.5, 0, point.y - 34];
}

function FieldLines() {
  const segments = useMemo(() => {
    const coordinates: number[] = [];
    const add = (a: Point, b: Point) => {
      const [ax, , az] = pitchWorld(a);
      const [bx, , bz] = pitchWorld(b);
      coordinates.push(ax, 0.035, az, bx, 0.035, bz);
    };
    const rect = (x0: number, y0: number, x1: number, y1: number) => {
      add({ x: x0, y: y0 }, { x: x1, y: y0 });
      add({ x: x1, y: y0 }, { x: x1, y: y1 });
      add({ x: x1, y: y1 }, { x: x0, y: y1 });
      add({ x: x0, y: y1 }, { x: x0, y: y0 });
    };
    rect(0.7, 0.7, 104.3, 67.3);
    add({ x: 52.5, y: 0.7 }, { x: 52.5, y: 67.3 });
    rect(0.7, 13.84, 17.2, 54.16);
    rect(87.8, 13.84, 104.3, 54.16);
    rect(0.7, 24.84, 6.2, 43.16);
    rect(98.8, 24.84, 104.3, 43.16);
    for (let i = 0; i < 96; i += 1) {
      const theta = (i / 96) * Math.PI * 2;
      const next = ((i + 1) / 96) * Math.PI * 2;
      add(
        { x: 52.5 + 9.15 * Math.cos(theta), y: 34 + 9.15 * Math.sin(theta) },
        { x: 52.5 + 9.15 * Math.cos(next), y: 34 + 9.15 * Math.sin(next) },
      );
    }
    return new Float32Array(coordinates);
  }, []);
  const geometry = useMemo(() => {
    const result = new THREE.BufferGeometry();
    result.setAttribute("position", new THREE.BufferAttribute(segments, 3));
    return result;
  }, [segments]);
  return (
    <lineSegments geometry={geometry}>
      <lineBasicMaterial color="#e5f4dc" transparent opacity={0.92} />
    </lineSegments>
  );
}

function ActiveActor({ event }: { event: MatchEvent }) {
  const [x, , z] = pitchWorld(event.location);
  const destination = event.destination;
  const dx = destination ? destination.x - event.location.x : 0;
  const dz = destination ? destination.y - event.location.y : 0;
  const distance = Math.hypot(dx, dz);
  const angle = Math.atan2(dx, dz);
  return (
    <group position={[x, 0, z]}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.045, 0]}>
        <ringGeometry args={[1.6, 2.1, 48]} />
        <meshBasicMaterial color="#b6e64b" side={THREE.DoubleSide} />
      </mesh>
      <group rotation={[0, angle, 0]}>
        <mesh position={[0, 1.22, 0]} castShadow>
          <capsuleGeometry args={[0.43, 0.9, 4, 8]} />
          <meshStandardMaterial color="#58bde5" roughness={0.7} />
        </mesh>
        <mesh position={[0, 2.15, 0]} castShadow>
          <sphereGeometry args={[0.33, 12, 10]} />
          <meshStandardMaterial color="#edc49d" roughness={0.9} />
        </mesh>
        {[-0.25, 0.25].map((leg) => (
          <mesh key={leg} position={[leg, 0.45, 0]} castShadow>
            <capsuleGeometry args={[0.15, 0.65, 3, 6]} />
            <meshStandardMaterial color="#173a4c" />
          </mesh>
        ))}
      </group>
      <mesh position={[0.9, 0.35, 1]}>
        <sphereGeometry args={[0.32, 12, 10]} />
        <meshStandardMaterial color="#f2f4e9" roughness={0.65} />
      </mesh>
      {destination && distance > 0 ? (
        <mesh
          position={[dx / 2, 0.08, dz / 2]}
          rotation={[-Math.PI / 2, 0, -angle]}
        >
          <planeGeometry args={[0.21, distance]} />
          <meshBasicMaterial color="#b6e64b" side={THREE.DoubleSide} />
        </mesh>
      ) : null}
    </group>
  );
}

export function BroadcastPitchScene({ event }: { event: MatchEvent | null }) {
  return (
    <div className="broadcast-webgl" aria-label="Three-dimensional tactical pitch">
      <Canvas
        orthographic
        camera={{ position: [0, 105, 24], zoom: 5.2, near: 0.1, far: 260 }}
        dpr={[1, 1.5]}
        shadows
        gl={{ antialias: true, alpha: false, powerPreference: "low-power" }}
      >
        <color attach="background" args={["#061409"]} />
        <ambientLight intensity={1.7} />
        <directionalLight position={[-25, 75, -22]} intensity={3.2} castShadow shadow-mapSize={[1024, 1024]} />
        <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[105, 68]} />
          <meshStandardMaterial color="#21502b" roughness={1} />
        </mesh>
        {Array.from({ length: 8 }, (_, index) => (
          <mesh
            key={index}
            rotation={[-Math.PI / 2, 0, 0]}
            position={[-45.94 + index * 13.125, 0.012, 0]}
          >
            <planeGeometry args={[13.12, 68]} />
            <meshStandardMaterial color={index % 2 === 0 ? "#275a31" : "#1c4526"} roughness={1} />
          </mesh>
        ))}
        <FieldLines />
        {event ? <ActiveActor event={event} /> : null}
      </Canvas>
    </div>
  );
}
