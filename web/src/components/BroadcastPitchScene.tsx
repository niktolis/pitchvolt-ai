import { Canvas, useThree } from "@react-three/fiber";
import { useEffect, useLayoutEffect, useMemo } from "react";
import * as THREE from "three";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";
import { LineSegments2 } from "three/addons/lines/LineSegments2.js";
import { LineSegmentsGeometry } from "three/addons/lines/LineSegmentsGeometry.js";
import type { MatchEvent } from "../api/types";
import {
  broadcastCameraPosition,
  eventPath,
  FIELD_HEIGHT,
  FIELD_WIDTH,
  toWorld,
  type PitchPoint,
} from "./pitch-geometry";

function BroadcastCamera() {
  const { camera, size } = useThree();

  useLayoutEffect(() => {
    if (!(camera instanceof THREE.PerspectiveCamera) || !size.height) return;
    camera.fov = 40;
    camera.aspect = size.width / size.height;
    camera.position.copy(broadcastCameraPosition(camera.aspect));
    camera.lookAt(0, 0, 0);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
  }, [camera, size.width, size.height]);

  return null;
}

function Turf() {
  const texture = useMemo(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 1024;
    canvas.height = 664;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.fillStyle = "#275d30";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    for (let stripe = 0; stripe < 10; stripe += 1) {
      ctx.fillStyle = stripe % 2 ? "#26582e" : "#31723b";
      ctx.fillRect(stripe * 102.4, 0, 103, 664);
    }

    // Seeded blades and wear: reproducible texture with no external asset/API.
    let seed = 453991;
    const random = () => {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    for (let i = 0; i < 32000; i += 1) {
      const x = random() * 1024;
      const y = random() * 664;
      const light = random() > 0.53;
      ctx.strokeStyle = light ? "rgba(170,210,116,0.16)" : "rgba(4,35,10,0.18)";
      ctx.lineWidth = 0.5 + random() * 0.65;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + (random() - 0.5) * 2.1, y - 0.9 - random() * 2.2);
      ctx.stroke();
    }

    const vignette = ctx.createRadialGradient(512, 240, 70, 512, 332, 700);
    vignette.addColorStop(0, "rgba(171,233,125,0.07)");
    vignette.addColorStop(1, "rgba(0,12,4,0.34)");
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const map = new THREE.CanvasTexture(canvas);
    map.colorSpace = THREE.SRGBColorSpace;
    map.anisotropy = 8;
    return map;
  }, []);

  useEffect(() => () => texture?.dispose(), [texture]);

  return (
    <>
      <mesh position={[0, -0.46, 0]} receiveShadow>
        <boxGeometry args={[FIELD_WIDTH + 2.6, 0.9, FIELD_HEIGHT + 2.6]} />
        <meshStandardMaterial color="#0b2410" roughness={1} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[FIELD_WIDTH, FIELD_HEIGHT]} />
        <meshStandardMaterial map={texture} color="#ffffff" roughness={0.98} />
      </mesh>
    </>
  );
}

function FieldMarkings() {
  const lines = useMemo(() => {
    const points: number[] = [];
    const add = (a: PitchPoint, b: PitchPoint) => {
      const from = toWorld(a);
      const to = toWorld(b);
      points.push(from.x, 0.055, from.z, to.x, 0.055, to.z);
    };
    const rectangle = (a: number, b: number, c: number, d: number) => {
      add({ x: a, y: b }, { x: c, y: b });
      add({ x: c, y: b }, { x: c, y: d });
      add({ x: c, y: d }, { x: a, y: d });
      add({ x: a, y: d }, { x: a, y: b });
    };
    rectangle(0.7, 0.7, 104.3, 67.3);
    add({ x: 52.5, y: 0.7 }, { x: 52.5, y: 67.3 });
    rectangle(0.7, 13.84, 17.2, 54.16);
    rectangle(87.8, 13.84, 104.3, 54.16);
    rectangle(0.7, 24.84, 6.2, 43.16);
    rectangle(98.8, 24.84, 104.3, 43.16);

    for (let step = 0; step < 120; step += 1) {
      const start = (step * Math.PI * 2) / 120;
      const end = ((step + 1) * Math.PI * 2) / 120;
      add(
        { x: 52.5 + Math.cos(start) * 9.15, y: 34 + Math.sin(start) * 9.15 },
        { x: 52.5 + Math.cos(end) * 9.15, y: 34 + Math.sin(end) * 9.15 },
      );
    }

    const geometry = new LineSegmentsGeometry();
    geometry.setPositions(points);
    const material = new LineMaterial({
      color: "#f2ffe6",
      linewidth: 0.17,
      worldUnits: true,
      transparent: true,
      opacity: 0.9,
    });
    return new LineSegments2(geometry, material);
  }, []);

  useEffect(
    () => () => {
      lines.geometry.dispose();
      lines.material.dispose();
    },
    [lines],
  );

  return <primitive object={lines} />;
}

function PlayerModel({ event }: { event: MatchEvent }) {
  const position = toWorld(event.location);
  const heading = event.destination
    ? Math.atan2(event.destination.x - event.location.x, event.destination.y - event.location.y)
    : 0;

  return (
    <group position={position}>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.082, 0]}>
        <ringGeometry args={[1.75, 2.15, 64]} />
        <meshBasicMaterial color="#b6e64b" side={THREE.DoubleSide} toneMapped={false} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.076, 0]}>
        <circleGeometry args={[1.5, 48]} />
        <meshBasicMaterial color="#a8f72c" transparent opacity={0.12} depthWrite={false} />
      </mesh>
      <group rotation={[0, heading, 0]}>
        <mesh position={[0, 1.35, 0]} castShadow>
          <capsuleGeometry args={[0.47, 0.85, 4, 12]} />
          <meshStandardMaterial color="#43aee7" roughness={0.78} />
        </mesh>
        <mesh position={[0, 1.64, 0.4]} castShadow>
          <boxGeometry args={[0.56, 0.18, 0.035]} />
          <meshStandardMaterial color="#e9f8ff" />
        </mesh>
        <mesh position={[0, 2.22, 0]} castShadow>
          <sphereGeometry args={[0.32, 14, 12]} />
          <meshStandardMaterial color="#e8ba8e" roughness={0.82} />
        </mesh>
        <mesh position={[0, 2.43, -0.09]} castShadow>
          <sphereGeometry args={[0.325, 12, 8, 0, Math.PI * 2, 0, Math.PI * 0.43]} />
          <meshStandardMaterial color="#2b2321" />
        </mesh>
        {[-0.57, 0.57].map((side) => (
          <group key={side}>
            <mesh position={[side, 1.43, 0]} rotation={[0, 0, side * 0.55]} castShadow>
              <capsuleGeometry args={[0.19, 0.65, 4, 8]} />
              <meshStandardMaterial color="#47b0e6" />
            </mesh>
            <mesh position={[side / 2, 0.49, 0]} castShadow>
              <capsuleGeometry args={[0.19, 0.77, 4, 8]} />
              <meshStandardMaterial color="#143f60" />
            </mesh>
            <mesh position={[side / 2, 0.12, 0.2]} castShadow>
              <boxGeometry args={[0.35, 0.14, 0.57]} />
              <meshStandardMaterial color="#ecfae5" />
            </mesh>
          </group>
        ))}
      </group>
      <mesh position={[0.9, 0.37, 1.1]} castShadow>
        <sphereGeometry args={[0.32, 12, 12]} />
        <meshStandardMaterial color="#ffffff" roughness={0.45} />
      </mesh>
    </group>
  );
}

function Trajectory({ event }: { event: MatchEvent }) {
  const path = eventPath(event.location, event.destination);
  if (!path) return null;
  const start = path.start.clone().setY(0.18);
  const end = path.end.clone().setY(0.18);
  const direction = end.clone().sub(start).normalize();
  const rotation = new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    direction,
  );
  const center = start.clone().add(end).multiplyScalar(0.5);

  return (
    <group>
      <mesh position={center} quaternion={rotation}>
        <cylinderGeometry args={[0.15, 0.15, path.length, 10]} />
        <meshBasicMaterial color="#c4ff56" toneMapped={false} />
      </mesh>
      <mesh position={[center.x, 0.12, center.z]} quaternion={rotation}>
        <cylinderGeometry args={[0.38, 0.38, path.length, 10]} />
        <meshBasicMaterial color="#9aff24" transparent opacity={0.17} depthWrite={false} />
      </mesh>
      <mesh position={end} quaternion={rotation}>
        <coneGeometry args={[0.52, 1.45, 12]} />
        <meshBasicMaterial color="#c4ff56" toneMapped={false} />
      </mesh>
    </group>
  );
}

export function BroadcastPitchScene({ event }: { event: MatchEvent | null }) {
  return (
    <div className="broadcast-webgl" role="img" aria-label="Perspective-rendered tactical football pitch">
      <Canvas
        camera={{ fov: 40, position: [0, 120, 80], near: 0.1, far: 420 }}
        dpr={[1, 1.5]}
        shadows
        gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
      >
        <BroadcastCamera />
        <color attach="background" args={["#06140b"]} />
        <hemisphereLight args={["#ddf8d5", "#091b10", 2.15]} />
        <ambientLight intensity={0.43} />
        <directionalLight
          position={[-35, 76, 18]}
          intensity={3.15}
          castShadow
          shadow-mapSize={[1024, 1024]}
          shadow-camera-left={-70}
          shadow-camera-right={70}
          shadow-camera-top={55}
          shadow-camera-bottom={-55}
          shadow-bias={-0.0001}
        />
        <directionalLight position={[35, 70, -45]} intensity={1.5} color="#c8edb1" />
        <Turf />
        <FieldMarkings />
        {event ? (
          <>
            <Trajectory event={event} />
            <PlayerModel event={event} />
          </>
        ) : null}
      </Canvas>
      <div className="pitch-illumination" aria-hidden="true" />
    </div>
  );
}
