import { Html } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";
import { LineSegments2 } from "three/addons/lines/LineSegments2.js";
import { LineSegmentsGeometry } from "three/addons/lines/LineSegmentsGeometry.js";
import type { MatchEvent } from "../api/types";
import { clockLabel, displayName } from "../domain/presentation";
import type { BallActionContext } from "../domain/ballAction";
import {
  actionCameraPose,
  FIELD_HEIGHT,
  FIELD_WIDTH,
  isSourcePitchPoint,
  type PitchPoint,
  sourceActorHeading,
  sourceArrow,
  toWorld,
} from "./pitch-geometry";

function BroadcastCamera({ focus }: { focus: PitchPoint | null }) {
  const { camera, size } = useThree();
  const lookAt = useRef(new THREE.Vector3());
  const initialized = useRef(false);
  const pose = useMemo(
    () => actionCameraPose(size.width / Math.max(size.height, 1), focus),
    [size.width, size.height, focus],
  );

  useLayoutEffect(() => {
    if (!(camera instanceof THREE.PerspectiveCamera) || !size.height) return;
    camera.fov = 40;
    camera.aspect = size.width / size.height;
    camera.updateProjectionMatrix();
    if (!initialized.current) {
      camera.position.copy(pose.position);
      lookAt.current.copy(pose.target);
      camera.lookAt(lookAt.current);
      camera.updateMatrixWorld();
      initialized.current = true;
    }
  }, [camera, size.width, size.height, pose]);

  useFrame((_, delta) => {
    if (!(camera instanceof THREE.PerspectiveCamera) || !initialized.current) return;
    // Only the camera moves between source observations; player positions never interpolate.
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const alpha = reduceMotion ? 1 : 1 - Math.exp(-4.5 * Math.min(delta, 0.1));
    camera.position.lerp(pose.position, alpha);
    lookAt.current.lerp(pose.target, alpha);
    camera.lookAt(lookAt.current);
  });

  return null;
}

function Turf() {
  const texture = useMemo(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 1024;
    canvas.height = 664;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.fillStyle = "#1c4825";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    for (let stripe = 0; stripe < 10; stripe += 1) {
      ctx.fillStyle = stripe % 2 ? "#1a4323" : "#265b30";
      ctx.fillRect(stripe * 102.4, 0, 103, 664);
    }

    // Seeded blades and wear: reproducible texture with no external asset/API.
    let seed = 453991;
    const random = () => {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    for (let i = 0; i < 46000; i += 1) {
      const x = random() * 1024;
      const y = random() * 664;
      const light = random() > 0.53;
      ctx.strokeStyle = light ? "rgba(188,226,136,0.22)" : "rgba(4,25,9,0.29)";
      ctx.lineWidth = 0.5 + random() * 0.65;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + (random() - 0.5) * 2.1, y - 0.9 - random() * 2.2);
      ctx.stroke();
    }

    const vignette = ctx.createRadialGradient(512, 240, 70, 512, 332, 700);
    vignette.addColorStop(0, "rgba(177,231,123,0.09)");
    vignette.addColorStop(1, "rgba(0,12,4,0.40)");
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
      {/* The extended grass apron is stadium infrastructure, not an inferred playable field. */}
      <mesh position={[0, -0.13, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[FIELD_WIDTH + 180, FIELD_HEIGHT + 160]} />
        <meshStandardMaterial map={texture} color="#a1c89a" roughness={1} />
      </mesh>
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

/** Fixed stadium infrastructure, not inferred football actor positions. */
function GoalFrame({ side }: { side: -1 | 1 }) {
  const x = side * (FIELD_WIDTH / 2 + 0.05);
  const depth = side * 1.8;
  const net = useMemo(() => {
    const coordinates: number[] = [];
    const add = (a: [number, number, number], b: [number, number, number]) => {
      coordinates.push(...a, ...b);
    };
    for (let i = 0; i <= 16; i += 1) {
      const z = -3.66 + (i * 7.32) / 16;
      add([x, 0.05, z], [x + depth, 0.05, z]);
      add([x + depth, 0.05, z], [x + depth, 2.44, z]);
      add([x, 2.44, z], [x + depth, 2.44, z]);
    }
    for (let i = 0; i <= 7; i += 1) {
      const y = (i * 2.44) / 7;
      add([x + depth, y, -3.66], [x + depth, y, 3.66]);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(coordinates, 3));
    return geometry;
  }, [x, depth]);

  useEffect(() => () => net.dispose(), [net]);

  return (
    <group>
      {[-3.66, 3.66].map((z) => (
        <mesh key={z} position={[x, 1.22, z]} castShadow>
          <cylinderGeometry args={[0.075, 0.075, 2.44, 8]} />
          <meshStandardMaterial color="#f0f6ee" roughness={0.55} />
        </mesh>
      ))}
      <mesh position={[x, 2.44, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.075, 0.075, 7.32, 8]} />
        <meshStandardMaterial color="#f0f6ee" roughness={0.55} />
      </mesh>
      <lineSegments geometry={net}>
        <lineBasicMaterial color="#d8e8dd" transparent opacity={0.23} depthWrite={false} />
      </lineSegments>
    </group>
  );
}

function PlayerModel({
  event,
  color,
  actorLabel,
  actorEmblem,
}: {
  event: MatchEvent;
  color?: string;
  actorLabel?: string;
  actorEmblem?: string;
}) {
  const position = toWorld(event.location);
  const heading = sourceActorHeading(event.location, event.destination);

  return (
    <group position={position}>
      <Html position={[2.8, 3.5, 0]} distanceFactor={23} style={{ pointerEvents: "none" }}>
        <div className="pitch-source-actor-label">
          {actorEmblem ? (
            <span
              className="source-actor-crest"
              style={{ backgroundColor: color ?? "#234c38" }}
              aria-hidden="true"
            >
              {actorEmblem}
            </span>
          ) : null}
          <span className="source-actor-text">
            <strong>{actorLabel ?? displayName(event.player_id)}</strong>
            <small>Recorded {clockLabel(event.clock_ms)}</small>
          </span>
        </div>
      </Html>
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
          <meshStandardMaterial color={color ?? "#43aee7"} roughness={0.78} />
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
              <meshStandardMaterial color={color ?? "#47b0e6"} />
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
    </group>
  );
}

/** A highlighted event-contact indicator: not live ball tracking or a flight path. */
function RecordedBallContact({ contact }: { contact: BallActionContext }) {
  if (!contact.location) return null;
  const position = toWorld(contact.location);
  return (
    <group position={position}>
      <mesh position={[0, 0.235, 0]} castShadow>
        <sphereGeometry args={[0.235, 20, 14]} />
        <meshStandardMaterial color="#f7fff7" roughness={0.65} />
      </mesh>
      <mesh position={[0, 0.235, 0]}>
        <icosahedronGeometry args={[0.239, 1]} />
        <meshBasicMaterial color="#192523" wireframe transparent opacity={0.45} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.048, 0]}>
        <ringGeometry args={[0.58, 0.72, 36]} />
        <meshBasicMaterial color="#ffffff" transparent opacity={0.6} depthWrite={false} />
      </mesh>
    </group>
  );
}

function Trajectory({ event }: { event: MatchEvent }) {
  const arrow = sourceArrow(event.location, event.destination);
  if (!arrow) return null;
  const rotation = new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    arrow.direction,
  );
  const shaftCenter = arrow.shaftCenter.clone().setY(0.17);
  const arrowCenter = arrow.arrowCenter.clone().setY(0.17);

  return (
    <group>
      <mesh position={shaftCenter} quaternion={rotation}>
        <cylinderGeometry args={[0.14, 0.14, arrow.shaftLength, 10]} />
        <meshBasicMaterial color="#c4ff56" toneMapped={false} />
      </mesh>
      <mesh position={shaftCenter} quaternion={rotation}>
        <cylinderGeometry args={[0.38, 0.38, arrow.shaftLength, 10]} />
        <meshBasicMaterial color="#b6e64b" transparent opacity={0.14} depthWrite={false} />
      </mesh>
      <mesh position={arrowCenter} quaternion={rotation}>
        <coneGeometry args={[0.57, arrow.arrowLength, 12]} />
        <meshBasicMaterial color="#c4ff56" toneMapped={false} />
      </mesh>
    </group>
  );
}

export function BroadcastPitchScene({
  event,
  actorColor,
  actorLabel,
  actorEmblem,
  ballContact,
}: {
  event: MatchEvent | null;
  actorColor?: string;
  actorLabel?: string;
  actorEmblem?: string;
  ballContact?: BallActionContext | null;
}) {
  return (
    <div
      className="broadcast-webgl"
      role="img"
      aria-label="Perspective-rendered tactical football pitch"
    >
      <Canvas
        camera={{ fov: 40, position: [0, 120, 80], near: 0.1, far: 420 }}
        dpr={[1, 1.5]}
        shadows
        gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
      >
        <BroadcastCamera
          focus={event && isSourcePitchPoint(event.location) ? event.location : null}
        />
        <color attach="background" args={["#06140b"]} />
        <hemisphereLight args={["#d5ecca", "#06170e", 1.4]} />
        <ambientLight intensity={0.24} />
        <directionalLight
          position={[-35, 76, 18]}
          intensity={2.5}
          castShadow
          shadow-mapSize={[1024, 1024]}
          shadow-camera-left={-70}
          shadow-camera-right={70}
          shadow-camera-top={55}
          shadow-camera-bottom={-55}
          shadow-bias={-0.0001}
        />
        <directionalLight position={[35, 70, -45]} intensity={1.15} color="#c8edb1" />
        <Turf />
        <FieldMarkings />
        <GoalFrame side={-1} />
        <GoalFrame side={1} />
        {ballContact?.location ? <RecordedBallContact contact={ballContact} /> : null}
        {event && isSourcePitchPoint(event.location) && event.player_id.trim() ? (
          <>
            <Trajectory event={event} />
            <PlayerModel
              event={event}
              color={actorColor}
              actorLabel={actorLabel}
              actorEmblem={actorEmblem}
            />
          </>
        ) : null}
      </Canvas>
      <div className="pitch-illumination" aria-hidden="true" />
    </div>
  );
}
