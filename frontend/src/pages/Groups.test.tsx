import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import Groups from "./Groups";
import api from "../api/client";
import { renderWithProviders } from "../test/renderWithProviders";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
  },
}));

describe("Groups page", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
  });

  it("renders group standings", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: [
        {
          group_letter: "A",
          standings: [
            {
              team_id: 1,
              team_name: "Mexico",
              fifa_code: "MEX",
              played: 0,
              won: 0,
              drawn: 0,
              lost: 0,
              goals_for: 0,
              goals_against: 0,
              goal_difference: 0,
              points: 0,
            },
          ],
        },
      ],
    });

    renderWithProviders(<Groups />);

    await waitFor(() => {
      expect(screen.getByText("MEX")).toBeInTheDocument();
    });
  });
});
