import { describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import axios from "axios";

import ForgotPassword from "./ForgotPassword";
import { renderWithProviders } from "../test/renderWithProviders";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("axios", () => ({
  default: {
    post: vi.fn(),
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
    })),
  },
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: null, loading: false }),
}));

describe("ForgotPassword page", () => {
  it("shows success after reset request", async () => {
    vi.mocked(axios.post).mockResolvedValueOnce({ data: {} });

    renderWithProviders(<ForgotPassword />);

    const textboxes = screen.getAllByRole("textbox");
    fireEvent.change(textboxes[0], { target: { value: "alice" } });
    fireEvent.change(textboxes[1], { target: { value: "alice@example.com" } });
    const passwords = document.querySelectorAll('input[type="password"]');
    fireEvent.change(passwords[0], { target: { value: "newsecret1" } });
    fireEvent.change(passwords[1], { target: { value: "newsecret1" } });
    fireEvent.click(screen.getByRole("button", { name: /save new password/i }));

    await waitFor(() => {
      expect(screen.getByText(/password was updated|sign in now/i)).toBeInTheDocument();
    });
  });
});
