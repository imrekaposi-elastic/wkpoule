import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import Register from "./Register";
import { renderWithProviders } from "../test/renderWithProviders";

const register = vi.fn();

vi.mock("../context/AuthContext", async () => {
  const actual = await vi.importActual<typeof import("../context/AuthContext")>(
    "../context/AuthContext",
  );
  return {
    ...actual,
    useAuth: () => ({ user: null, loading: false, register }),
  };
});

describe("Register page", () => {
  it("validates matching passwords before submit", async () => {
    renderWithProviders(<Register />);

    const textboxes = screen.getAllByRole("textbox");
    fireEvent.change(textboxes[0], { target: { value: "bob" } });
    fireEvent.change(textboxes[1], { target: { value: "bob@example.com" } });
    const passwords = document.querySelectorAll('input[type="password"]');
    fireEvent.change(passwords[0], { target: { value: "secret12" } });
    fireEvent.change(passwords[1], { target: { value: "different" } });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText("Passwords do not match")).toBeInTheDocument();
    });
    expect(register).not.toHaveBeenCalled();
  });
});
