import { describe, expect, it } from "vitest";
import { heroAssetForEvent } from "./heroAssetSelection";

describe("CC0 Key Moment model selection guard", () => {
  it.each(["pass", "carry", "shot", "pressure", "turnover", "goal"] as const)(
    "keeps procedural fallback for %s while no verified self-hosted GLB is supplied",
    (kind) => {
      expect(heroAssetForEvent(kind)).toBeNull();
    },
  );
});
