import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import Profile from "./Profile";
import { renderWithProviders } from "../test/renderWithProviders";

const refreshUser = vi.fn().mockResolvedValue(undefined);

vi.mock("../api/client", () => ({
  default: {
    patch: vi.fn().mockResolvedValue({
      data: {
        id: 1,
        username: "alice",
        email: "alice@example.com",
        is_admin: false,
        preferred_language: "en",
      },
    }),
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
});
