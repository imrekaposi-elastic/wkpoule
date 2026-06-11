import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import Dashboard from "./Dashboard";
import api from "../api/client";
import { renderWithProviders, sampleUser } from "../test/renderWithProviders";
import { mockApiResponses } from "../test/mockApiResponses";
import { sampleMatch } from "../test/fixtures";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("../api/authenticatedPoll", () => ({
  beforeAuthenticatedPoll: vi.fn(async () => true),
  shouldSkipAuthenticatedPoll: vi.fn(() => false),
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
    expect(screen.getByText(/the world cup has begun/i)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /fifa world cup 2026/i })).toBeInTheDocument();
  });

  it("shows the next match to predict", async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("next-needing-prediction")) {
        return Promise.resolve({ data: sampleMatch });
      }
      if (url.includes("/rankings/me")) {
        return Promise.resolve({
          data: {
            rank: 1,
            user_id: 1,
            username: "alice",
            total_points: 10,
            correct_results: 2,
            correct_scores: 1,
            correct_goal_counts: 0,
            predictions_made: 5,
          },
        });
      }
      if (url.includes("/subgroups/mine")) return Promise.resolve({ data: [] });
      if (url.includes("/matches/by-day")) return Promise.resolve({ data: [sampleMatch] });
      if (url.includes("/matches/calendar-meta")) {
        return Promise.resolve({
          data: {
            first_kickoff_utc: sampleMatch.kickoff_utc,
            first_match_local_date: "2026-06-11",
          },
        });
      }
      if (url.includes("/predictions/mine/brief")) return Promise.resolve({ data: [] });
      return Promise.resolve({ data: [] });
    });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/NED/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: /make prediction/i })).toHaveAttribute(
      "href",
      "/matches/1",
    );
  });

  it("shows completion message when all predictions are done", async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("next-needing-prediction")) {
        return Promise.resolve({ data: null });
      }
      if (url.includes("/rankings/me")) {
        return Promise.resolve({
          data: {
            rank: 1,
            user_id: 1,
            username: "alice",
            total_points: 100,
            correct_results: 50,
            correct_scores: 10,
            correct_goal_counts: 5,
            predictions_made: 104,
          },
        });
      }
      if (url.includes("/subgroups/mine")) {
        return Promise.resolve({
          data: [{ id: 3, name: "Office", role: "owner", member_count: 2 }],
        });
      }
      if (url.includes("/subgroups/3")) {
        return Promise.resolve({
          data: {
            id: 3,
            name: "Office",
            my_role: "owner",
            members: [],
            rankings: {
              items: [
                {
                  rank: 1,
                  user_id: 1,
                  username: "alice",
                  total_points: 12,
                  correct_results: 1,
                  correct_scores: 0,
                  correct_goal_counts: 0,
                  predictions_made: 10,
                },
              ],
              total: 1,
              page: 1,
              page_size: 20,
              total_pages: 1,
            },
          },
        });
      }
      if (url.includes("/matches/by-day")) return Promise.resolve({ data: [] });
      if (url.includes("/matches/calendar-meta")) {
        return Promise.resolve({
          data: {
            first_kickoff_utc: sampleMatch.kickoff_utc,
            first_match_local_date: "2026-06-11",
          },
        });
      }
      if (url.includes("/predictions/mine/brief")) return Promise.resolve({ data: [] });
      return Promise.resolve({ data: [] });
    });

    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getAllByText(/completed all predictions/i).length).toBeGreaterThan(0);
    });
    expect(screen.getByText("Office")).toBeInTheDocument();
  });

  it("refreshes subgroup data when mine-changed fires", async () => {
    renderWithProviders(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/welcome back, alice/i)).toBeInTheDocument();
    });

    vi.mocked(api.get).mockClear();
    window.dispatchEvent(new Event("subgroups-mine-changed"));

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/subgroups/mine");
    });
  });
});
