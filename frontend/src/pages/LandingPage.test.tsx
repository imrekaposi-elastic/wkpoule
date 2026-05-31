import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";

import LandingPage from "./LandingPage";
import { renderWithProviders } from "../test/renderWithProviders";

describe("LandingPage", () => {
  it("renders hero and feature sections", () => {
    renderWithProviders(<LandingPage />);

    expect(screen.getAllByRole("link", { name: /create your account/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: /log in/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/2026/).length).toBeGreaterThan(0);
  });
});
