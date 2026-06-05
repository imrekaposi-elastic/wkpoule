import { describe, expect, it, vi } from "vitest";

const startTransaction = vi.fn(() => ({
  addLabels: vi.fn(),
  end: vi.fn(),
}));

vi.mock("@elastic/apm-rum", () => ({
  apm: { startTransaction },
}));

import { trackMilestones } from "./trackMilestone";

describe("trackMilestones", () => {
  it("does nothing for empty or missing keys", () => {
    trackMilestones(undefined);
    trackMilestones([]);
    expect(startTransaction).not.toHaveBeenCalled();
  });

  it("emits a RUM transaction per milestone key", () => {
    trackMilestones(["first_prediction", "group_complete"]);

    expect(startTransaction).toHaveBeenCalledTimes(2);
    expect(startTransaction).toHaveBeenNthCalledWith(
      1,
      "goal:first_prediction",
      "user-interaction",
    );
    expect(startTransaction).toHaveBeenNthCalledWith(
      2,
      "goal:group_complete",
      "user-interaction",
    );
  });
});
