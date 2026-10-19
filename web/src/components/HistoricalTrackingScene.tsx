import { Canvas, useThree } from "@react-three/fiber";
import { useLayoutEffect, useMemo } from "react";
import * as THREE from "three";
import type { HistoricalClip, SourceFrame } from "../domain/historicalReplay";
import { FieldMarkings, GoalFrame, Turf } from "./BroadcastPitchScene";
import { FootballActorAvatar } from "./FootballActorAvatar";
import { actionCameraPose, toWorld } from "./pitch-geometry";

function FixedSourceCamera({
  focus,
}: {
  focus: { x: number; y: number } | null;
}) {
  const { camera, size } = useThree();
  const pose = useMemo(
    () => actionCameraPose(size.width / Math.max(1, size.height), focus),
    [size.width, size.height, focus],
  );

  useLayoutEffect(() => {
    if (!(camera instanceof THREE.PerspectiveCamera) || !size.height) return;
    camera.fov = 40;
    camera.aspect = size.width / size.height;
    camera.updateProjectionMatrix();
    camera.position.copy(pose.position);
    camera.lookAt(pose.target);
    camera.updateMatrixWorld();
  }, [camera, size.width, size.height, pose]);
  return null;
}

/**
 * Each position is the current exact source sample. Model anatomy and neutral
 * orientation are illustrative, but source coordinates are never interpolated.
 */
function SourceActors({
  clip,
  frame,
}: {
  clip: HistoricalClip;
  frame: SourceFrame;
}) {
  const homes = clip.match.teams.find((t) => t.role === "home")?.id;
  return (
    <>
      {frame.players_xy_m.map((xy, index) => {
        if (!xy) return null;
        const player = clip.roster[index];
        if (!player) return null;
        const p = toWorld({ x: xy[0], y: xy[1] });
        return (
          <group key={player.source_player_id} position={[p.x, 0, p.z]}>
            <FootballActorAvatar
              kitColor={player.source_team_id === homes ? "#f6f6f0" : "#d5263e"}
            />
          </group>
        );
      })}
      {/* Ball vertical coordinate is source-measured Z, not a drawn pass arc. */}
      <group position={[
        frame.ball_xyz_m[0] - 52.5,
        frame.ball_xyz_m[2],
        frame.ball_xyz_m[1] - 34,
      ]}>
        <mesh castShadow>
          <sphereGeometry args={[0.22, 16, 12]} />
          <meshStandardMaterial color="#ffffff" roughness={0.6} />
        </mesh>
        <mesh>
          <icosahedronGeometry args={[0.222, 1]} />
          <meshBasicMaterial color="#192b2a" wireframe transparent opacity={0.5} />
        </mesh>
      </group>
    </>
  );
}

export function HistoricalTrackingScene({
  clip,
  frame,
  shotFocus = false,
}: {
  clip: HistoricalClip;
  frame: SourceFrame;
  shotFocus?: boolean;
}) {
  const focus = shotFocus
    ? { x: frame.ball_xyz_m[0], y: frame.ball_xyz_m[1] }
    : null;

  return (
    <div
      className="broadcast-webgl historical-webgl"
      role="img"
      aria-label={shotFocus
        ? "3D view of the observed historical shot location"
        : "3D source-observed 22-player and measured-ball football replay"}
    >
      <Canvas
        camera={{ fov: 40, position: [0, 125, 80], near: 0.1, far: 450 }}
        dpr={[1, 1.35]}
        shadows={false}
        gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
      >
        <FixedSourceCamera focus={focus} />
        <color attach="background" args={["#06140b"]} />
        <hemisphereLight args={["#d5ecca", "#07170e", 1.75]} />
        <ambientLight intensity={0.48} />
        <directionalLight position={[-35, 76, 18]} intensity={2.5} />
        <directionalLight position={[35, 70, -45]} intensity={0.95} color="#c8edb1" />
        <Turf />
        <FieldMarkings />
        <GoalFrame side={-1} />
        <GoalFrame side={1} />
        <SourceActors clip={clip} frame={frame} />
      </Canvas>
      <div className="pitch-illumination" aria-hidden="true" />
    </div>
  );
}
