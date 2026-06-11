import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import MatchDayCalendar from "./MatchDayCalendar";
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

describe("MatchDayCalendar", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/matches/calendar-meta")) {
        return Promise.resolve({
          data: {
            first_kickoff_utc: sampleMatch.kickoff_utc,
            first_match_local_date: "2026-06-11",
          },
        });
      }
      if (url.includes("/matches/by-day")) {
        return Promise.resolve({ data: [sampleMatch] });
      }
      if (url.includes("/predictions/mine/brief")) {
        return Promise.resolve({
          data: [{ match_id: 1, home_score: 2, away_score: 1 }],
        });
      }
      if (url === "/matches") {
        return Promise.resolve({
          data: {
            items: [sampleMatch],
            total: 1,
            page: 1,
            page_size: 1,
            total_pages: 1,
          },
        });
      }
      return Promise.resolve({ data: [] });
    });
  });

  it("renders calendar heading", async () => {
    renderWithProviders(<MatchDayCalendar />);

    await waitFor(() => {
      expect(screen.getByText(/match calendar/i)).toBeInTheDocument();
    });
  });

  it("loads matches for the selected day", async () => {
    renderWithProviders(<MatchDayCalendar />);

    fireEvent.click(screen.getByRole("button", { name: /next day/i }));

    await waitFor(() => {
      expect(screen.getByText(/Netherlands/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/your prediction: 2 – 1/i)).toBeInTheDocument();
  });

  it("moves to the next calendar day", async () => {
    renderWithProviders(<MatchDayCalendar />);

    await waitFor(() => {
      expect(screen.getByText(/match calendar/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /next day/i }));

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/matches/by-day", {
        params: expect.objectContaining({ date: expect.any(String) }),
      });
    });
  });
});
