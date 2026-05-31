import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import Venues from "./Venues";
import api from "../api/client";
import { renderWithProviders } from "../test/renderWithProviders";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
  },
}));

describe("Venues page", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
  });

  it("renders venue cards with schedule", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: [
        {
          id: 1,
          name: "MetLife Stadium",
          city: "East Rutherford",
          country: "USA",
          capacity: 82500,
          latitude: 40.8,
          longitude: -74.1,
          year_built: 2010,
          rating: 4,
          city_attractiveness: 5,
          expected_temp_celsius: 24,
          image_url: null,
          review_en: "Large modern stadium.",
          review_nl: "Groot modern stadion.",
          accessibility_en: "Accessible transit.",
          accessibility_nl: "Bereikbaar met OV.",
          matches: [
            {
              match_id: 1,
              match_number: 1,
              stage: "group",
              group_letter: "A",
              kickoff_utc: "2026-06-11T18:00:00Z",
              home_team_name: "Mexico",
              away_team_name: "Canada",
              home_team_code: "MEX",
              away_team_code: "CAN",
              attractiveness_stars: 4,
            },
          ],
        },
      ],
    });

    renderWithProviders(<Venues />);

    await waitFor(() => {
      expect(screen.getByText("MetLife Stadium")).toBeInTheDocument();
    });
    expect(screen.getByText(/Mexico/)).toBeInTheDocument();
    expect(screen.getByText(/Large modern stadium/)).toBeInTheDocument();
  });
});
