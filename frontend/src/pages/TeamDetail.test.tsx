import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import TeamDetailPage from "./TeamDetail";
import api from "../api/client";
import { renderWithProviders } from "../test/renderWithProviders";
import { Route, Routes } from "react-router-dom";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
  },
}));

describe("TeamDetail page", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
  });

  it("renders team profile and squad", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        id: 1,
        name: "Netherlands",
        fifa_code: "NED",
        group_letter: "F",
        world_ranking: 7,
        flag_url: "https://example.com/ned.svg",
        qualification_en: "Qualified via UEFA.",
        qualification_nl: "Gekwalificeerd via UEFA.",
        qualification_pt: "Classificado",
        qualification_de: "Qualifiziert",
        qualification_es: "Clasificado",
        qualification_it: "Qualificato",
        qualification_he: "Qualified",
        strengths_en: "Midfield\nWings",
        strengths_nl: "Middenveld",
        strengths_pt: "Meio",
        strengths_de: "Mittelfeld",
        strengths_es: "Medio",
        strengths_it: "Centrocampo",
        strengths_he: "Midfield",
        weaknesses_en: "Counters",
        weaknesses_nl: "Counters",
        weaknesses_pt: "Contra",
        weaknesses_de: "Konter",
        weaknesses_es: "Contra",
        weaknesses_it: "Contropiedi",
        weaknesses_he: "Counters",
        qualification_data: {
          competition: { en: "UEFA Group G" },
          standings: [],
          results: [],
        },
        players: [
          {
            id: 10,
            name: "Virgil van Dijk",
            position: "DF",
            shirt_number: 4,
            club: "Liverpool",
            caps: 75,
          },
        ],
      },
    });

    renderWithProviders(
      <Routes>
        <Route path="/teams/:fifaCode" element={<TeamDetailPage />} />
      </Routes>,
      { route: "/teams/NED" },
    );

    await waitFor(() => {
      expect(screen.getByText("Virgil van Dijk")).toBeInTheDocument();
    });
    expect(screen.getByText(/Qualified via UEFA/)).toBeInTheDocument();
  });

  it("shows not found for missing teams", async () => {
    vi.mocked(api.get).mockRejectedValueOnce({ response: { status: 404 } });

    renderWithProviders(
      <Routes>
        <Route path="/teams/:fifaCode" element={<TeamDetailPage />} />
      </Routes>,
      { route: "/teams/XYZ" },
    );

    await waitFor(() => {
      expect(screen.getByText(/not found|niet gevonden/i)).toBeInTheDocument();
    });
  });
});
