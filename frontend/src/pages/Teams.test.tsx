import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import Teams from "./Teams";
import api from "../api/client";
import { renderWithProviders } from "../test/renderWithProviders";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
  },
}));

describe("Teams page", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
  });

  it("renders grouped teams", async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: [
        {
          id: 1,
          name: "Netherlands",
          fifa_code: "NED",
          group_letter: "F",
          world_ranking: 7,
          flag_url: "https://example.com/ned.svg",
          qualification_en: "Qualified",
          qualification_nl: "Gekwalificeerd",
          qualification_pt: "Classificado",
          qualification_de: "Qualifiziert",
          qualification_es: "Clasificado",
          qualification_it: "Qualificato",
          qualification_he: "Qualified",
        },
      ],
    });

    renderWithProviders(<Teams />);

    await waitFor(() => {
      expect(screen.getByText("Netherlands")).toBeInTheDocument();
    });
    expect(screen.getByText(/NED/)).toBeInTheDocument();
  });

  it("shows an error state when loading fails", async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error("network"));

    renderWithProviders(<Teams />);

    await waitFor(() => {
      expect(screen.getByText(/could not load teams|Teams konnten niet geladen/i)).toBeInTheDocument();
    });
  });
});
