import { useGLTF } from "@react-three/drei";
import { Component, Suspense, useEffect, useMemo, type ReactNode } from "react";
import * as THREE from "three";
import type { MatchEvent } from "../api/types";
import { heroAssetForEvent, type VerifiedHeroAsset } from "../domain/heroAssetSelection";
import { KeyMomentAthlete } from "./KeyMomentAthlete";

interface HeroProps {
  eventType: MatchEvent["event_type"];
  color?: string;
}

interface FailureBoundaryProps {
  children: ReactNode;
  fallback: ReactNode;
}

class HeroAssetErrorBoundary extends Component<FailureBoundaryProps, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

/** Only loaded when the manifest contains a verified, self-hosted GLB. */
function StaticVerifiedHero({ asset, color }: { asset: VerifiedHeroAsset; color?: string }) {
  const gltf = useGLTF(asset.url);
  const { clone, ownedMaterials } = useMemo(() => {
    const scene = gltf.scene.clone(true);
    const materials: THREE.Material[] = [];
    scene.traverse((node) => {
      if (!(node instanceof THREE.Mesh)) return;
      node.castShadow = true;
      node.receiveShadow = true;
      const original = node.material;
      const replaceKit = (material: THREE.Material) => {
        if (material.name !== asset.kitMaterial || !(material instanceof THREE.MeshStandardMaterial)) {
          return material;
        }
        const editable = material.clone();
        // The optimizer must preserve a shirt-specific material name.
        // This changes only the shirt, never skin/hair; the jersey is illustrative,
        // not a licensed replica of the real club's official kit.
        if (color && /^#[0-9a-fA-F]{6}$/.test(color)) editable.color.set(color);
        materials.push(editable);
        return editable;
      };
      node.material = Array.isArray(original)
        ? original.map(replaceKit)
        : replaceKit(original);
    });
    return { clone: scene, ownedMaterials: materials };
  }, [gltf.scene, asset.kitMaterial, color]);

  useEffect(
    () => () => {
      for (const material of ownedMaterials) material.dispose();
    },
    [ownedMaterials],
  );

  return <primitive object={clone} scale={1.83 / asset.heightMetres} />;
}

/**
 * Verified model first; the current procedural avatar is an always-present
 * loading/error/fallback path. Does not create player positions or joint samples.
 */
export function KeyMomentHero({ eventType, color }: HeroProps) {
  const asset = heroAssetForEvent(eventType);
  const fallback = <KeyMomentAthlete kitColor={color} eventType={eventType} />;
  if (!asset) return fallback;

  return (
    <HeroAssetErrorBoundary key={asset.url} fallback={fallback}>
      <Suspense fallback={fallback}>
        <StaticVerifiedHero asset={asset} color={color} />
      </Suspense>
    </HeroAssetErrorBoundary>
  );
}
