import { describe, expect, it } from "vitest";
import { heroAssetForEvent, isUnobservedHeroProp } from "./heroAssetSelection";

const cases = [
  ["carry", "stride-61e0538d75e289c1.glb"],
  ["pressure", "stride-61e0538d75e289c1.glb"],
  ["pass", "strike-4d09e5934a5ba79c.glb"],
  ["shot", "strike-4d09e5934a5ba79c.glb"],
  ["goal", "strike-4d09e5934a5ba79c.glb"],
  ["turnover", "neutral-59ee4cbe96e07698.glb"],
] as const;

describe("same-family source-verified action-specific CC0 footballers", () => {
  it.each(cases)("selects a provenance-pinned %s portrait without inventing motion", (event, filename) => {
    const model = heroAssetForEvent(event);
    expect(model).not.toBeNull();
    expect(model?.url).toBe(`/assets/hero/${filename}`);
    expect(model?.license).toBe("CC0-1.0");
    expect(model?.sourceUrl).toContain("www.innerscene.com/tools/library/3d-parts/");
    expect(model?.kitMaterial).toBe("Micah | top");
    expect(model?.bytes).toBeLessThan(4 * 1024 * 1024);
    expect(model?.sha256).toMatch(/^[0-9a-f]{64}$/);
  });

  it("does not hide the actor while suppressing decorative soccer ball and shirt number", () => {
    expect(isUnobservedHeroProp("Soccer ball | pentagon and hexagon panels")).toBe(true);
    expect(isUnobservedHeroProp("soccer_ball_prop")).toBe(true);
    expect(isUnobservedHeroProp("Soccer jersey number")).toBe(true);
    expect(isUnobservedHeroProp("Micah | anatomical body")).toBe(false);
    expect(isUnobservedHeroProp("Soccer footballer")).toBe(false);
  });
});
