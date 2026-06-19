import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

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

const rankingsPage = {
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
};

function mockRankingsApis() {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === "/subgroups/directory") {
      return Promise.resolve({
        data: [{ id: 7, name: "Friends", member_count: 4, membership_status: "member" }],
      });
    }
    if (url === "/rankings") {
      return Promise.resolve({ data: rankingsPage });
    }
    return Promise.reject(new Error(`Unexpected GET ${url}`));
  });
}

describe("Rankings page", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
  });

  it("renders participant rankings", async () => {
    mockRankingsApis();

    renderWithProviders(<Rankings />);

    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
    });
    expect(screen.getByText("24")).toBeInTheDocument();
  });

  it("loads subgroup-filtered rankings when a subleague is selected", async () => {
    mockRankingsApis();

    renderWithProviders(<Rankings />);

    await waitFor(() => {
      expect(screen.getByText("Select league:")).toBeInTheDocument();
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByRole("combobox"), { target: { value: "7" } });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/rankings", {
        params: { page: 1, page_size: 20, subgroup_id: 7 },
      });
    });
  });
});
