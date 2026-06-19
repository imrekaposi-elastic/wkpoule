import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import Matches from "./Matches";
import api from "../api/client";
import { renderWithProviders } from "../test/renderWithProviders";
import { sampleMatch } from "../test/fixtures";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
  },
}));

const virtualGroup = {
  group_letter: "A",
  third_place_qualifies: true,
  standings: [
    {
      team_id: 1,
      team_name: "Netherlands",
      fifa_code: "NED",
      played: 1,
      won: 1,
      drawn: 0,
      lost: 0,
      goals_for: 2,
      goals_against: 1,
      goal_difference: 1,
      points: 3,
    },
  ],
};

describe("Matches page", () => {
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
      if (url === "/predictions/mine/brief") {
        return Promise.resolve({ data: [] });
      }
      if (url === "/predictions/virtual-groups") {
        return Promise.resolve({ data: [virtualGroup] });
      }
      return Promise.resolve({ data: [] });
    });
  });

  it("renders match list heading", async () => {
    renderWithProviders(<Matches />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /match schedule/i })).toBeInTheDocument();
    });
  });

  it("renders seeded matches and filters by search", async () => {
    renderWithProviders(<Matches />);

    await waitFor(() => {
      expect(screen.getByText(/Netherlands/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText(/search/i), {
      target: { value: "belgium" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^search$/i }));

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/matches", {
        params: expect.objectContaining({ search: "belgium" }),
      });
    });
  });

  it("shows matches before virtual standings finish loading", async () => {
    let resolveVirtual: ((value: { data: typeof virtualGroup[] }) => void) | undefined;
    const virtualPromise = new Promise<{ data: typeof virtualGroup[] }>((resolve) => {
      resolveVirtual = resolve;
    });

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
      if (url === "/predictions/mine/brief") {
        return Promise.resolve({ data: [] });
      }
      if (url === "/predictions/virtual-groups") {
        return virtualPromise;
      }
      return Promise.resolve({ data: [] });
    });

    renderWithProviders(<Matches />);

    const groupSelect = screen.getAllByRole("combobox")[1];
    fireEvent.change(groupSelect, { target: { value: "A" } });

    await waitFor(() => {
      expect(screen.getByText(/Netherlands/i)).toBeInTheDocument();
    });

    expect(screen.queryByText(/your virtual standings/i)).not.toBeInTheDocument();

    resolveVirtual?.({ data: [virtualGroup] });

    await waitFor(() => {
      expect(screen.getByText(/your virtual standings/i)).toBeInTheDocument();
    });
  });
});
