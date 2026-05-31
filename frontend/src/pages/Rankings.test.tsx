import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import Rankings from "./Rankings";
import api from "../api/client";
import { renderWithProviders, sampleUser } from "../test/renderWithProviders";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
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

describe("Rankings page", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
  });

  it("renders participant rankings", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        items: [
          {
            rank: 1,
            user_id: 1,
            username: "alice",
            total_points: 24,
            correct_results: 3,
            correct_scores: 1,
            correct_goal_counts: 2,
            predictions_made: 5,
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });

    renderWithProviders(<Rankings />);

    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });
    expect(screen.getByText("24")).toBeInTheDocument();
  });
});
