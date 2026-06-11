import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import App from "./App";
import { renderWithProviders, sampleUser } from "./test/renderWithProviders";

vi.mock("./components/Navbar", () => ({
  default: () => <nav data-testid="navbar">Navbar</nav>,
}));

vi.mock("./pages/MatchDetail", () => ({
  default: () => <div>Match detail</div>,
}));

vi.mock("./pages/SubgroupDetail", () => ({
  default: () => <div>Subgroup detail</div>,
}));

vi.mock("./pages/AdminSettings", () => ({
  default: () => <div>Admin settings</div>,
}));

vi.mock("./pages/Dashboard", () => ({
  default: () => <div>Dashboard home</div>,
}));

vi.mock("./pages/LandingPage", () => ({
  default: () => <div>Landing page</div>,
}));

const useAuthMock = vi.fn();

vi.mock("./context/AuthContext", async () => {
  const actual = await vi.importActual<typeof import("./context/AuthContext")>(
    "./context/AuthContext",
  );
  return {
    ...actual,
    useAuth: () => useAuthMock(),
  };
});

describe("App routing", () => {
  beforeEach(() => {
    useAuthMock.mockReset();
  });

  it("shows landing page for guests", async () => {
    useAuthMock.mockReturnValue({ user: null, loading: false });

    renderWithProviders(<App />);

    await waitFor(() => {
      expect(screen.getByText("Landing page")).toBeInTheDocument();
    });
  });

  it("shows a loading spinner while auth is resolving", () => {
    useAuthMock.mockReturnValue({ user: null, loading: true });

    renderWithProviders(<App />);

    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("redirects unauthenticated users away from protected routes", async () => {
    useAuthMock.mockReturnValue({ user: null, loading: false });

    renderWithProviders(<App />, { route: "/matches" });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    });
  });

  it("shows dashboard for signed-in users on home", async () => {
    useAuthMock.mockReturnValue({ user: sampleUser, loading: false });

    renderWithProviders(<App />);

    await waitFor(() => {
      expect(screen.getByText("Dashboard home")).toBeInTheDocument();
    });
  });

  it("blocks non-admin users from admin routes", async () => {
    useAuthMock.mockReturnValue({ user: sampleUser, loading: false });

    renderWithProviders(<App />, { route: "/admin/scores" });

    await waitFor(() => {
      expect(screen.queryByText(/admin scores/i)).not.toBeInTheDocument();
    });
  });
});
