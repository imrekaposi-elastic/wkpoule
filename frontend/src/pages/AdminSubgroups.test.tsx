import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import AdminSubgroups from "./AdminSubgroups";
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

describe("AdminSubgroups page", () => {
  beforeEach(() => {
    mockApiResponses(api);
  });

  it("renders admin subgroup list", async () => {
    renderWithProviders(<AdminSubgroups />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /admin · subgroups/i })).toBeInTheDocument();
    });
  });
});
