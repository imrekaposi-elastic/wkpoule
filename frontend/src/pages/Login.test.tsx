import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import Login from "./Login";
import { renderWithProviders } from "../test/renderWithProviders";

const login = vi.fn();

vi.mock("../context/AuthContext", async () => {
  const actual = await vi.importActual<typeof import("../context/AuthContext")>(
    "../context/AuthContext",
  );
  return {
    ...actual,
    useAuth: () => ({ user: null, loading: false, login }),
  };
});

describe("Login page", () => {
  it("submits credentials", async () => {
    login.mockResolvedValueOnce(undefined);

    renderWithProviders(<Login />);

    fireEvent.change(screen.getByPlaceholderText("Enter your username"), {
      target: { value: "Alice" },
    });
    fireEvent.change(screen.getByPlaceholderText("Enter your password"), {
      target: { value: "secret12" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith("alice", "secret12");
    });
  });
});
