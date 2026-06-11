import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, renderHook, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";

import { AuthProvider, useAuth } from "./AuthContext";
import { sampleUser } from "../test/renderWithProviders";

const apiMocks = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
}));

vi.mock("../api/client", () => ({
  default: apiMocks,
  ensureFreshAccessToken: vi.fn(async () => localStorage.getItem("access_token")),
  msUntilAccessTokenRefresh: vi.fn(() => null),
}));

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe("AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
    apiMocks.get.mockReset();
    apiMocks.post.mockReset();
    apiMocks.patch.mockReset();
  });

  it("loads the current user when a token exists", async () => {
    localStorage.setItem("access_token", "token");
    apiMocks.get.mockResolvedValueOnce({ data: sampleUser });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user?.username).toBe("alice");
  });

  it("logs in and stores tokens", async () => {
    apiMocks.post.mockResolvedValueOnce({
      data: { access_token: "access", refresh_token: "refresh" },
    });
    apiMocks.get.mockResolvedValueOnce({ data: sampleUser });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login("alice", "secret12");
    });

    expect(localStorage.getItem("access_token")).toBe("access");
    expect(result.current.user?.username).toBe("alice");
  });

  it("logs out and clears tokens", async () => {
    localStorage.setItem("access_token", "token");
    apiMocks.get.mockResolvedValueOnce({ data: sampleUser });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.user).not.toBeNull());

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("access_token")).toBeNull();
  });

  it("registers a new user and logs in", async () => {
    apiMocks.post
      .mockResolvedValueOnce({ data: {} })
      .mockResolvedValueOnce({
        data: { access_token: "access", refresh_token: "refresh" },
      });
    apiMocks.get.mockResolvedValueOnce({ data: sampleUser });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.register("newbie", "new@example.com", "secret12", "nl");
    });

    expect(apiMocks.post).toHaveBeenCalledWith("/auth/register", {
      username: "newbie",
      email: "new@example.com",
      password: "secret12",
      preferred_language: "nl",
    });
    expect(result.current.user?.username).toBe("alice");
  });

  it("refreshes the current user profile", async () => {
    localStorage.setItem("access_token", "token");
    apiMocks.get
      .mockResolvedValueOnce({ data: sampleUser })
      .mockResolvedValueOnce({ data: { ...sampleUser, is_admin: true } });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.user).not.toBeNull());

    await act(async () => {
      await result.current.refreshUser();
    });

    expect(result.current.user?.is_admin).toBe(true);
  });

  it("clears tokens when profile refresh fails", async () => {
    localStorage.setItem("access_token", "token");
    localStorage.setItem("refresh_token", "refresh");
    apiMocks.get.mockResolvedValueOnce({ data: sampleUser });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.user).not.toBeNull());

    apiMocks.get.mockRejectedValueOnce(new Error("unauthorized"));
    await act(async () => {
      await result.current.refreshUser();
    });

    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("access_token")).toBeNull();
  });
});
