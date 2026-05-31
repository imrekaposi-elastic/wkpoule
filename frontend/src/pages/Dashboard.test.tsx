import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import Dashboard from "./Dashboard";
import api from "../api/client";
import { renderWithProviders, sampleUser } from "../test/renderWithProviders";
import { mockApiResponses } from "../test/mockApiResponses";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("../context/AuthContext", async () => {
  const actual = await vi.importActual<typeof import("../context/AuthContext")>(
    "../context/AuthContext",
  );
  return {
    ...actual,
    useAuth: () => ({ user: sampleUser, loading: false }),
  };
});

describe("Dashboard page", () => {
  beforeEach(() => {
    mockApiResponses(api);
  });

  it("renders welcome and ranking summary", async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/welcome back, alice/i)).toBeInTheDocument();
    });
    expect(screen.getByText("#2")).toBeInTheDocument();
  });
});
