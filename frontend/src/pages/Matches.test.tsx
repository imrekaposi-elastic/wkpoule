import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import Matches from "./Matches";
import api from "../api/client";
import { renderWithProviders } from "../test/renderWithProviders";
import { mockApiResponses } from "../test/mockApiResponses";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

describe("Matches page", () => {
  beforeEach(() => {
    mockApiResponses(api);
  });

  it("renders match list heading", async () => {
    renderWithProviders(<Matches />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /match schedule/i })).toBeInTheDocument();
    });
  });
});
