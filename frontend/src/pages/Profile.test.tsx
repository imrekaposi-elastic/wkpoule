import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import Profile from "./Profile";
import api from "../api/client";
import { renderWithProviders } from "../test/renderWithProviders";

const refreshUser = vi.fn().mockResolvedValue(undefined);

vi.mock("../api/client", () => ({
  default: {
    patch: vi.fn(),
  },
}));

vi.mock("../context/AuthContext", async () => {
  const actual = await vi.importActual<typeof import("../context/AuthContext")>(
    "../context/AuthContext",
  );
  return {
    ...actual,
    useAuth: () => ({
      user: {
        id: 1,
        username: "alice",
        email: "alice@example.com",
        is_admin: false,
        preferred_language: "en",
        include_in_rankings: true,
      },
      loading: false,
      refreshUser,
    }),
  };
});

describe("Profile page", () => {
  it("shows no-changes message when submitting unchanged values", async () => {
    renderWithProviders(<Profile />);

    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(screen.getByText("No changes to save.")).toBeInTheDocument();
    });
  });

  it("updates profile details and refreshes auth state", async () => {
    vi.mocked(api.patch).mockResolvedValueOnce({
      data: {
        id: 1,
        username: "alice2",
        email: "new@example.com",
        is_admin: false,
        preferred_language: "en",
        access_token: "new-access",
        refresh_token: "new-refresh",
      },
    });

    renderWithProviders(<Profile />);

    fireEvent.change(screen.getByDisplayValue("alice"), {
      target: { value: "alice2" },
    });
    fireEvent.change(screen.getByDisplayValue("alice@example.com"), {
      target: { value: "new@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith("/auth/me", {
        username: "alice2",
        email: "new@example.com",
      });
    });
    expect(refreshUser).toHaveBeenCalled();
  });

  it("shows API error detail when update fails", async () => {
    vi.mocked(api.patch).mockRejectedValueOnce({
      response: { data: { detail: "Email already registered" } },
    });

    renderWithProviders(<Profile />);

    fireEvent.change(screen.getByDisplayValue("alice@example.com"), {
      target: { value: "taken@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(screen.getByText("Email already registered")).toBeInTheDocument();
    });
  });
});
