import { beforeEach, describe, expect, it, vi } from "vitest";

const clientMocks = vi.hoisted(() => ({
  ensureFreshAccessToken: vi.fn(),
  hasStoredAuthTokens: vi.fn(),
}));

vi.mock("./client", () => ({
  ensureFreshAccessToken: clientMocks.ensureFreshAccessToken,
  hasStoredAuthTokens: clientMocks.hasStoredAuthTokens,
}));

import { beforeAuthenticatedPoll, shouldSkipAuthenticatedPoll } from "./authenticatedPoll";

describe("authenticatedPoll", () => {
  beforeEach(() => {
    clientMocks.ensureFreshAccessToken.mockReset();
    clientMocks.hasStoredAuthTokens.mockReset();
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
  });

  it("skips polling when the tab is hidden", () => {
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "hidden",
    });
    clientMocks.hasStoredAuthTokens.mockReturnValue(true);

    expect(shouldSkipAuthenticatedPoll()).toBe(true);
  });

  it("skips polling when no tokens are stored", () => {
    clientMocks.hasStoredAuthTokens.mockReturnValue(false);

    expect(shouldSkipAuthenticatedPoll()).toBe(true);
  });

  it("returns false before polling when tokens exist and tab is visible", async () => {
    clientMocks.hasStoredAuthTokens.mockReturnValue(true);
    clientMocks.ensureFreshAccessToken.mockResolvedValue("token");

    await expect(beforeAuthenticatedPoll()).resolves.toBe(true);
  });

  it("returns false when token refresh fails", async () => {
    clientMocks.hasStoredAuthTokens.mockReturnValue(true);
    clientMocks.ensureFreshAccessToken.mockResolvedValue(null);

    await expect(beforeAuthenticatedPoll()).resolves.toBe(false);
  });
});
