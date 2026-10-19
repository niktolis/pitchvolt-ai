import { describe, expect, it } from "vitest";
import { heroAssetForEvent } from "./heroAssetSelection";

describe("source-verified CC0 Key Moment asset selection", () => {
  it.each(["pass", "carry", "shot", "pressure", "turnover", "goal"] as const)(
    "uses the pinned static footballer for %s until a dedicated pose model is verified",
    (kind) => {
      const model = heroAssetForEvent(kind);
      expect(model).not.toBeNull();
      expect(model?.url).toBe("/assets/hero/neutral-5bb8a63f2824d84c.glb");
      expect(model?.sha256).toBe(
        "5bb8a63f2824d84c4f8a346ca11d6af0eefd1854050cfa3dde4fb12a134c6591",
      );
      expect(model?.sourceSha256).toBe(
        "773cfa73bbcf659d7044934aaeacf1c3c9a49ae2955a51f56de7ad61ad1b6ffb",
      );
      expect(model?.license).toBe("CC0-1.0");
      expect(model?.kitMaterial).toBe("Micah | top");
      expect(model?.bytes).toBeLessThan(4 * 1024 * 1024);
      expect(model?.sourceUrl).toContain("www.innerscene.com/tools/library/3d-parts/");
    },
  );
});
