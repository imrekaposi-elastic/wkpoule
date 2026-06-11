import { beforeEach, describe, expect, it, vi } from "vitest";

function makeJwt(payload: Record<string, unknown>): string {
  const encode = (value: object) =>
    btoa(JSON.stringify(value)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  return `${encode({ alg: "HS256", typ: "JWT" })}.${encode(payload)}.sig`;
}

const axiosMocks = vi.hoisted(() => {
  const requestUse = vi.fn();
  const responseUse = vi.fn();
  const instanceCall = vi.fn();
  const post = vi.fn();

  const create = vi.fn(() => {
    const instance = ((config: unknown) => instanceCall(config)) as {
      (config: unknown): ReturnType<typeof instanceCall>;
      interceptors: {
        request: { use: typeof requestUse };
        response: { use: typeof responseUse };
      };
    };
    instance.interceptors = {
      request: { use: requestUse },
      response: { use: responseUse },
    };
    return instance;
  });

  return { requestUse, responseUse, instanceCall, post, create };
});

vi.mock("axios", () => ({
  default: {
    create: axiosMocks.create,
    post: axiosMocks.post,
  },
}));

describe("api client interceptors", () => {
  beforeEach(async () => {
    vi.resetModules();
    localStorage.clear();
    axiosMocks.requestUse.mockClear();
    axiosMocks.responseUse.mockClear();
    axiosMocks.instanceCall.mockClear();
    axiosMocks.post.mockReset();
    axiosMocks.create.mockClear();
    await import("./client");
  });

  it("adds bearer token to outgoing requests", async () => {
    const token = makeJwt({ exp: Math.floor(Date.now() / 1000) + 3600, sub: "1" });
    localStorage.setItem("access_token", token);
    const onRequest = axiosMocks.requestUse.mock.calls[0][0] as (config: {
      url: string;
      headers: Record<string, string>;
    }) => Promise<typeof config>;

    const updated = await onRequest({ url: "/teams", headers: {} });

    expect(updated.headers.Authorization).toBe(`Bearer ${token}`);
  });

  it("proactively refreshes before sending protected requests", async () => {
    localStorage.setItem(
      "access_token",
      makeJwt({ exp: Math.floor(Date.now() / 1000) + 30, sub: "1" }),
    );
    localStorage.setItem("refresh_token", "refresh-abc");
    axiosMocks.post.mockResolvedValueOnce({
      data: { access_token: "fresh", refresh_token: "refresh-new" },
    });

    const onRequest = axiosMocks.requestUse.mock.calls[0][0] as (config: {
      url: string;
      headers: Record<string, string>;
    }) => Promise<typeof config>;

    const updated = await onRequest({ url: "/subgroups/mine", headers: {} });

    expect(axiosMocks.post).toHaveBeenCalledWith("/api/auth/refresh", {
      refresh_token: "refresh-abc",
    });
    expect(updated.headers.Authorization).toBe("Bearer fresh");
  });

  it("refreshes token on 401 and retries the original request", async () => {
    localStorage.setItem("access_token", "expired");
    localStorage.setItem("refresh_token", "refresh-abc");

    axiosMocks.post.mockResolvedValueOnce({
      data: { access_token: "fresh", refresh_token: "refresh-new" },
    });
    axiosMocks.instanceCall.mockResolvedValueOnce({ data: { ok: true } });

    const onRejected = axiosMocks.responseUse.mock.calls[0][1] as (error: {
      response: { status: number };
      config: { url: string; headers: Record<string, string>; _retry?: boolean };
    }) => Promise<unknown>;

    const result = await onRejected({
      response: { status: 401 },
      config: { url: "/teams", headers: {}, _retry: false },
    });

    expect(axiosMocks.post).toHaveBeenCalledWith("/api/auth/refresh", {
      refresh_token: "refresh-abc",
    });
    expect(localStorage.getItem("access_token")).toBe("fresh");
    expect(localStorage.getItem("refresh_token")).toBe("refresh-new");
    expect(axiosMocks.instanceCall).toHaveBeenCalledTimes(1);
    expect(result).toEqual({ data: { ok: true } });
  });

  it("returns existing token when not expiring soon", async () => {
    const token = makeJwt({ exp: Math.floor(Date.now() / 1000) + 3600, sub: "1" });
    localStorage.setItem("access_token", token);

    const { ensureFreshAccessToken } = await import("./client");
    await expect(ensureFreshAccessToken()).resolves.toBe(token);
    expect(axiosMocks.post).not.toHaveBeenCalled();
  });

  it("returns null when refresh fails for an expiring token", async () => {
    localStorage.setItem(
      "access_token",
      makeJwt({ exp: Math.floor(Date.now() / 1000) + 30, sub: "1" }),
    );
    localStorage.setItem("refresh_token", "refresh-abc");
    axiosMocks.post.mockRejectedValueOnce(new Error("refresh failed"));

    const { ensureFreshAccessToken } = await import("./client");
    await expect(ensureFreshAccessToken()).resolves.toBeNull();
  });

  it("computes delay until proactive refresh", async () => {
    const exp = Math.floor(Date.now() / 1000) + 600;
    localStorage.setItem("access_token", makeJwt({ exp, sub: "1" }));

    const { msUntilAccessTokenRefresh } = await import("./client");
    const delay = msUntilAccessTokenRefresh();
    expect(delay).not.toBeNull();
    expect(delay!).toBeGreaterThan(0);
    expect(delay!).toBeLessThanOrEqual(8 * 60 * 1000);
  });
});
