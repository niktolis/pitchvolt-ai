import { ContactShadows } from "@react-three/drei";
import { Canvas, useThree } from "@react-three/fiber";
import { useLayoutEffect, useState } from "react";
import * as THREE from "three";
import type { MatchEvent } from "../api/types";
import { ballActionAtCursor } from "../domain/ballAction";
import { displayName } from "../domain/presentation";
import { FieldMarkings, GoalFrame, RecordedBallContact, Turf } from "./BroadcastPitchScene";
import { KeyMomentAthlete } from "./KeyMomentAthlete";
import { KeyMomentGrass } from "./KeyMomentGrass";
import {
  isSourcePitchPoint,
  keyMomentCameraPose,
  type PitchPoint,
  sourceActorHeading,
  toWorld,
} from "./pitch-geometry";

interface KeyMomentProps {
  event: MatchEvent | null;
  cursorMs: number;
  actorLabel?: string;
  actorColor?: string;
  actorEmblem?: string;
}

/** Static, source-framed camera. Demand-rendered, not a second replay clock. */
function KeyMomentCamera({ focus }: { focus: PitchPoint }) {
  const { camera, size, invalidate } = useThree();
  useLayoutEffect(() => {
    const pose = keyMomentCameraPose(focus);
    if (!pose || !size.height || !(camera instanceof THREE.PerspectiveCamera)) return;
    camera.position.copy(pose.position);
    camera.lookAt(pose.target);
    camera.updateMatrixWorld();
    camera.aspect = size.width / size.height;
    camera.updateProjectionMatrix();
    invalidate();
  }, [camera, focus, invalidate, size.height, size.width]);

  return null;
}

export function SourceMomentPreview({
  event,
  cursorMs,
  actorLabel,
  actorColor,
  actorEmblem,
}: KeyMomentProps) {
  const actor = event?.player_id.trim() && isSourcePitchPoint(event.location) ? event : null;
  const destination = actor && isSourcePitchPoint(actor.destination) ? actor.destination : null;
  const ball = ballActionAtCursor(actor, cursorMs);
  const [hasWebGL] = useState(() => {
    try {
      return Boolean(document.createElement("canvas").getContext("webgl2"));
    } catch {
      return false;
    }
  });

  return (
    <div className="key-moment-scene key-moment-source-scene">
      {actor && hasWebGL ? (
        <div
          className="key-moment-3d"
          role="img"
          aria-label={`3D editorial view of recorded action by ${actorLabel ?? displayName(actor.player_id)} at ${actor.clock_ms} milliseconds; not source footage`}
        >
          <Canvas
            frameloop="demand"
            dpr={[1, 1.5]}
            shadows
            camera={{ fov: 34, near: 0.1, far: 160, position: [0, 5, 9] }}
            gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
            onCreated={({ gl }) => {
              gl.toneMapping = THREE.ACESFilmicToneMapping;
              gl.toneMappingExposure = 1.12;
            }}
          >
            <KeyMomentCamera focus={actor.location} />
            <color attach="background" args={["#07130d"]} />
            <fog attach="fog" args={["#07130d", 17, 62]} />
            <hemisphereLight args={["#e6f4e8", "#112419", 0.95]} />
            <ambientLight intensity={0.22} />
            {/* Art-directed stadium floodlights; not measured lighting from this game. */}
            <directionalLight
              position={[-7, 16, 10]}
              color="#f6ffe8"
              intensity={3.4}
              castShadow
              shadow-mapSize={[1024, 1024]}
              shadow-camera-left={-9}
              shadow-camera-right={9}
              shadow-camera-top={9}
              shadow-camera-bottom={-9}
              shadow-bias={-0.0004}
              shadow-normalBias={0.012}
            />
            <directionalLight position={[7, 8, -8]} color="#d0f7b0" intensity={2.0} />
            <directionalLight position={[-4, 5, -9]} color="#84aef1" intensity={0.6} />
            <Turf />
            <KeyMomentGrass focus={actor.location} />
            <FieldMarkings />
            <GoalFrame side={-1} />
            <GoalFrame side={1} />
            <ContactShadows
              position={[toWorld(actor.location).x, 0.012, toWorld(actor.location).z]}
              opacity={0.44}
              scale={6}
              blur={2.2}
              far={4}
              resolution={256}
              frames={1}
            />
            {ball?.location ? <RecordedBallContact contact={ball} /> : null}
            <group position={toWorld(actor.location)}>
              <group rotation={[0, sourceActorHeading(actor.location, actor.destination), 0]}>
                <KeyMomentAthlete kitColor={actorColor} eventType={actor.event_type} />
              </group>
            </group>
          </Canvas>
          <div className="key-moment-actor-tag" aria-hidden="true">
            {actorEmblem ? (
              <span
                className="source-actor-crest"
                style={{ backgroundColor: actorColor ?? "#234c38" }}
              >
                {actorEmblem}
              </span>
            ) : null}
            <strong>{actorLabel ?? displayName(actor.player_id)}</strong>
          </div>
        </div>
      ) : null}
      <svg
        className={actor && hasWebGL ? "key-moment-svg-fallback" : undefined}
        viewBox="0 0 105 68"
        role="img"
        aria-label={
          actor
            ? `Recorded event position for ${displayName(actor.player_id)} on the pitch`
            : "Key moment location unavailable"
        }
      >
        <defs>
          <marker
            id="moment-destination-tip"
            markerWidth="4"
            markerHeight="4"
            refX="4"
            refY="2"
            orient="auto"
          >
            <path d="M 0 0 L 4 2 L 0 4 Z" fill="#b6e64b" />
          </marker>
        </defs>
        <rect
          x="0.7"
          y="0.7"
          width="103.6"
          height="66.6"
          rx="1"
          fill="none"
          stroke="#d8eed2"
          strokeWidth=".45"
        />
        <line x1="52.5" y1="0.7" x2="52.5" y2="67.3" stroke="#d8eed2" strokeWidth=".4" />
        <circle cx="52.5" cy="34" r="9.15" fill="none" stroke="#d8eed2" strokeWidth=".4" />
        <rect
          x="0.7"
          y="13.84"
          width="16.5"
          height="40.32"
          fill="none"
          stroke="#d8eed2"
          strokeWidth=".4"
        />
        <rect
          x="87.8"
          y="13.84"
          width="16.5"
          height="40.32"
          fill="none"
          stroke="#d8eed2"
          strokeWidth=".4"
        />
        {actor && destination ? (
          <line
            x1={actor.location.x}
            y1={actor.location.y}
            x2={destination.x}
            y2={destination.y}
            stroke="#b6e64b"
            strokeWidth=".85"
            markerEnd="url(#moment-destination-tip)"
          />
        ) : null}
        {actor ? (
          <g transform={`translate(${actor.location.x} ${actor.location.y})`}>
            <circle r="4.2" fill="#b6e64b" fillOpacity=".2" />
            <circle r="2.5" fill="none" stroke="#b6e64b" strokeWidth=".7" />
            <circle r=".9" fill="#e9ffe0" />
          </g>
        ) : null}
      </svg>
      <span className="moment-provenance-label">
        {actor
          ? hasWebGL
            ? "3D editorial portrait · illustrated pose, recorded position"
            : "Recorded event actor · 2D fallback"
          : "No source position"}
      </span>
    </div>
  );
}
