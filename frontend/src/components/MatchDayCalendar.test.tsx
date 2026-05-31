import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import MatchDayCalendar from "./MatchDayCalendar";
import api from "../api/client";
import { renderWithProviders } from "../test/renderWithProviders";
import { mockApiResponses } from "../test/mockApiResponses";

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
    mockApiResponses(api);
  });

  it("renders calendar heading", async () => {
    renderWithProviders(<MatchDayCalendar />);

    await waitFor(() => {
      expect(screen.getByText(/match calendar/i)).toBeInTheDocument();
    });
  });
});
