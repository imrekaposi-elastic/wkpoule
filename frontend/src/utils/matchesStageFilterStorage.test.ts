import { describe, expect, it, beforeEach } from "vitest";

import {
  readMatchesStageFilter,
  writeMatchesStageFilter,
} from "./matchesStageFilterStorage";

describe("matchesStageFilterStorage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns empty filter when nothing is pinned", () => {
    expect(readMatchesStageFilter()).toEqual({
      stage: "",
      group: "",
      pinned: false,
    });
  });

  it("persists and restores pinned stage filter", () => {
    writeMatchesStageFilter("round_of_16", "", true);

    expect(readMatchesStageFilter()).toEqual({
      stage: "round_of_16",
      group: "",
      pinned: true,
    });
  });

  it("clears stored filter when unpinned", () => {
    writeMatchesStageFilter("round_of_16", "A", true);
    writeMatchesStageFilter("round_of_16", "A", false);

    expect(readMatchesStageFilter()).toEqual({
      stage: "",
      group: "",
      pinned: false,
    });
  });
});
