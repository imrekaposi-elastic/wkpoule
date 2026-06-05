import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import MatchPredictionsSummary from "./MatchPredictionsSummary";
import api from "../api/client";
import { renderWithProviders } from "../test/renderWithProviders";
import type { Team } from "../types";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
  },
}));

const homeTeam: Team = {
  id: 1,
  name: "Mexico",
  fifa_code: "MEX",
  group_letter: "A",
  world_ranking: 14,
  flag_url: "",
};

const awayTeam: Team = {
  id: 2,
  name: "Canada",
  fifa_code: "CAN",
  group_letter: "A",
  world_ranking: 48,
  flag_url: "",
};

describe("MatchPredictionsSummary", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
  });

  it("renders aggregated outcome counts", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        total: 5,
        home_win_count: 3,
        away_win_count: 1,
        draw_count: 1,
      },
    });

    renderWithProviders(
      <MatchPredictionsSummary matchId={42} homeTeam={homeTeam} awayTeam={awayTeam} />,
    );

    await waitFor(() => {
      expect(screen.getByText("Mexico win")).toBeInTheDocument();
      expect(screen.getByText("Canada win")).toBeInTheDocument();
      expect(screen.getByText("Draw")).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: /3 predictions.*Mexico win/i })).toHaveTextContent(
      "3",
    );
  });

  it("opens a paginated popup with user scores when a count is clicked", async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({
        data: {
          total: 2,
          home_win_count: 2,
          away_win_count: 0,
          draw_count: 0,
        },
      })
      .mockResolvedValueOnce({
        data: {
          items: [
            {
              user_id: 10,
              username: "alice",
              home_score: 2,
              away_score: 0,
              advance_team_id: null,
              points: null,
            },
          ],
          total: 1,
          page: 1,
          page_size: 10,
          total_pages: 1,
        },
      });

    renderWithProviders(
      <MatchPredictionsSummary matchId={42} homeTeam={homeTeam} awayTeam={awayTeam} />,
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /2 predictions.*Mexico win/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /2 predictions.*Mexico win/i }));

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/predictions/match/42/by-outcome", {
        params: { outcome: "home_win", page: 1, page_size: 10 },
      });
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByText("alice")).toBeInTheDocument();
      expect(screen.getByText("2 - 0")).toBeInTheDocument();
    });
  });
});
