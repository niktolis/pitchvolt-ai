import { Canvas, useThree } from "@react-three/fiber";
import { useLayoutEffect, useState } from "react";
import * as THREE from "three";
import type { MatchEvent } from "../api/types";
import { ballActionAtCursor } from "../domain/ballAction";
import { displayName } from "../domain/presentation";
import { FieldMarkings, GoalFrame, RecordedBallContact, Turf } from "./BroadcastPitchScene";
import { FootballActorAvatar } from "./FootballActorAvatar";
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
            dpr={[1, 1.25]}
            shadows
            camera={{ fov: 38, near: 0.1, far: 160, position: [0, 6, 9] }}
            gl={{ antialias: true, alpha: false, powerPreference: "low-power" }}
          >
            <KeyMomentCamera focus={actor.location} />
            <color attach="background" args={["#08190f"]} />
            <fog attach="fog" args={["#08190f", 22, 80]} />
            <hemisphereLight args={["#edffe6", "#05150c", 1.8]} />
            <ambientLight intensity={0.35} />
            <directionalLight
              position={[-12, 24, 15]}
              color="#f2ffe4"
              intensity={2.8}
              castShadow
              shadow-mapSize={[512, 512]}
              shadow-camera-left={-24}
              shadow-camera-right={24}
              shadow-camera-top={24}
              shadow-camera-bottom={-24}
            />
            <directionalLight position={[14, 12, -7]} color="#adff71" intensity={0.8} />
            <Turf />
            <FieldMarkings />
            <GoalFrame side={-1} />
            <GoalFrame side={1} />
            {ball?.location ? <RecordedBallContact contact={ball} /> : null}
            <group position={toWorld(actor.location)}>
              <group rotation={[0, sourceActorHeading(actor.location, actor.destination), 0]}>
                <FootballActorAvatar kitColor={actorColor} />
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
            ? "3D editorial reconstruction · recorded position"
            : "Recorded event actor · 2D fallback"
          : "No source position"}
      </span>
    </div>
  );
}
