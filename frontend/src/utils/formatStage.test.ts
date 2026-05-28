import { describe, expect, it } from "vitest";

import { formatStageSlug, formatStageSlugSpacesOnly } from "./formatStage";

describe("formatStageSlug", () => {
  it("title-cases underscore-separated slugs", () => {
    expect(formatStageSlug("round_of_16")).toBe("Round Of 16");
  });

  it("handles empty parts safely", () => {
    expect(formatStageSlug("group")).toBe("Group");
  });
});

describe("formatStageSlugSpacesOnly", () => {
  it("replaces underscores with spaces", () => {
    expect(formatStageSlugSpacesOnly("quarter_final")).toBe("quarter final");
  });
});
