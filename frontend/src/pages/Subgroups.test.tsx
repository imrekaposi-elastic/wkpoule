import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import Subgroups from "./Subgroups";
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

describe("Subgroups page", () => {
  beforeEach(() => {
    mockApiResponses(api);
  });

  it("renders subgroup hub", async () => {
    renderWithProviders(<Subgroups />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /^subgroup$/i })).toBeInTheDocument();
    });
  });
});
