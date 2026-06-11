import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import Matches from "./Matches";
import api from "../api/client";
import { renderWithProviders } from "../test/renderWithProviders";
import { sampleMatch } from "../test/fixtures";

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
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === "/matches") {
        return Promise.resolve({
          data: {
            items: [sampleMatch],
            total: 1,
            page: 1,
            page_size: 20,
            total_pages: 1,
          },
        });
      }
      return Promise.resolve({ data: [] });
    });
  });

  it("renders match list heading", async () => {
    renderWithProviders(<Matches />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /match schedule/i })).toBeInTheDocument();
    });
  });

  it("renders seeded matches and filters by search", async () => {
    renderWithProviders(<Matches />);

    await waitFor(() => {
      expect(screen.getByText(/Netherlands/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText(/search/i), {
      target: { value: "belgium" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^search$/i }));

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/matches", {
        params: expect.objectContaining({ search: "belgium" }),
      });
    });
  });
});
