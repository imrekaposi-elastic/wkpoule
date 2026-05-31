import { beforeEach, describe, expect, it, vi } from "vitest";

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

  it("adds bearer token to outgoing requests", () => {
    localStorage.setItem("access_token", "access-123");
    const onRequest = axiosMocks.requestUse.mock.calls[0][0] as (config: {
      headers: Record<string, string>;
    }) => typeof config;

    const config = { headers: {} as Record<string, string> };
    const updated = onRequest(config);

    expect(updated.headers.Authorization).toBe("Bearer access-123");
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
});
