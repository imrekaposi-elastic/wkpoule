import { describe, expect, it } from "vitest";
import { resolveApmEnvironment } from "./apmEnvironment";

describe("resolveApmEnvironment", () => {
  it("prefers runtime config over build-time and hostname", () => {
    expect(
      resolveApmEnvironment("acc-wc2026.apps.cloud.kaposi.net", "acc", "prd"),
    ).toBe("acc");
  });

  it("prefers acc hostname over build-time prd when runtime is empty", () => {
    expect(
      resolveApmEnvironment("acc-wc2026.apps.cloud.kaposi.net", undefined, "prd"),
    ).toBe("acc");
  });

  it("falls back to build-time when runtime is empty and hostname is not acc", () => {
    expect(resolveApmEnvironment("wc2026.apps.cloud.kaposi.net", "", "staging")).toBe(
      "staging",
    );
  });

  it("derives acc from hostname when no config is set", () => {
    expect(resolveApmEnvironment("acc-wc2026.apps.cloud.kaposi.net")).toBe("acc");
  });

  it("defaults to prd", () => {
    expect(resolveApmEnvironment("wc2026.apps.cloud.kaposi.net")).toBe("prd");
  });
});
