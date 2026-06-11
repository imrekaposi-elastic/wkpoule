import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import AdminScores from "./AdminScores";
import api from "../api/client";
import { renderWithProviders } from "../test/renderWithProviders";
import { sampleMatch } from "../test/fixtures";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

describe("AdminScores page", () => {
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
    vi.mocked(api.patch).mockResolvedValue({
      data: { ...sampleMatch, home_score: 2, away_score: 1, status: "completed" },
    });
  });

  it("loads matches and saves a score", async () => {
    renderWithProviders(<AdminScores />);

    await waitFor(() => {
      expect(screen.getByText(/NED vs BEL/i)).toBeInTheDocument();
    });

    const homeInput = screen.getAllByRole("spinbutton")[0];
    fireEvent.change(homeInput, { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: /apply/i }));

    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith("/matches/1/score", {
        home_score: 2,
        away_score: 0,
        status: "upcoming",
      });
    });
  });

  it("filters matches by search text", async () => {
    renderWithProviders(<AdminScores />);

    await waitFor(() => {
      expect(screen.getByText(/NED vs BEL/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText(/search/i), {
      target: { value: "zzz-no-match" },
    });

    expect(screen.getByText(/no matches/i)).toBeInTheDocument();
  });

  it("shows an error banner when save fails", async () => {
    vi.mocked(api.patch).mockRejectedValueOnce({
      response: { data: { detail: "Invalid score" } },
    });

    renderWithProviders(<AdminScores />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /apply/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /apply/i }));

    await waitFor(() => {
      expect(screen.getByText("Invalid score")).toBeInTheDocument();
    });
  });
});
