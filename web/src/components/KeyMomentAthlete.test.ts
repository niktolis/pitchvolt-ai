import { describe, expect, it } from "vitest";
import { editorialPoseForEvent } from "./KeyMomentAthlete";

describe("Key Moment editorial pose mapping", () => {
  it.each(["pass", "shot", "goal"] as const)(
    "renders %s with an explicitly illustrative strike pose",
    (action) => {
      expect(editorialPoseForEvent(action)).toBe("strike");
    },
  );

  it("maps carries and pressure into distinct editorial illustration categories", () => {
    expect(editorialPoseForEvent("carry")).toBe("stride");
    expect(editorialPoseForEvent("pressure")).toBe("defend");
  });

  it("remains neutral for unknown and possession-transition events", () => {
    expect(editorialPoseForEvent("turnover")).toBe("neutral");
  });
});
