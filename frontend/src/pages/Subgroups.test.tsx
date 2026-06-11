import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";

import Subgroups from "./Subgroups";
import api from "../api/client";
import { renderWithProviders, sampleUser } from "../test/renderWithProviders";
import { mockApiResponses } from "../test/mockApiResponses";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("../api/authenticatedPoll", () => ({
  beforeAuthenticatedPoll: vi.fn(async () => true),
  shouldSkipAuthenticatedPoll: vi.fn(() => false),
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

describe("Subgroups page", () => {
  beforeEach(() => {
    mockApiResponses(api);
  });

  it("renders subgroup hub", async () => {
    renderWithProviders(<Subgroups />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /^subgroup$/i })).toBeInTheDocument();
    });
  });

  it("creates a subgroup", async () => {
    renderWithProviders(<Subgroups />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/name/i)).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText(/name/i), {
      target: { value: "Office Pool" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^create$/i }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/subgroups", { name: "Office Pool" });
    });
  });

  it("accepts a pending invite", async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/subgroups/invites/pending")) {
        return Promise.resolve({
          data: [
            {
              id: 5,
              subgroup_id: 2,
              subgroup_name: "Friends",
              inviter_username: "bob",
              created_at: "2026-06-01T12:00:00Z",
            },
          ],
        });
      }
      if (url.includes("/subgroups/mine")) return Promise.resolve({ data: [] });
      if (url.includes("/subgroups/directory")) return Promise.resolve({ data: [] });
      if (url.includes("/subgroups/join-requests/incoming")) return Promise.resolve({ data: [] });
      return Promise.resolve({ data: [] });
    });

    renderWithProviders(<Subgroups />);

    await waitFor(() => {
      expect(screen.getByText(/friends/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /accept/i }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/subgroups/invites/5/accept");
    });
  });

  it("applies to join a public subgroup", async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/subgroups/directory")) {
        return Promise.resolve({
          data: [
            {
              id: 9,
              name: "Open Pool",
              member_count: 3,
              membership_status: "none",
            },
          ],
        });
      }
      if (url.includes("/subgroups/mine")) return Promise.resolve({ data: [] });
      if (url.includes("/subgroups/invites/pending")) return Promise.resolve({ data: [] });
      if (url.includes("/subgroups/join-requests/incoming")) return Promise.resolve({ data: [] });
      return Promise.resolve({ data: [] });
    });

    renderWithProviders(<Subgroups />);

    await waitFor(() => {
      expect(screen.getByText("Open Pool")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /apply/i }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/subgroups/9/join-requests");
    });
  });

  it("approves an incoming join request", async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/subgroups/join-requests/incoming")) {
        return Promise.resolve({
          data: [
            {
              id: 12,
              subgroup_id: 4,
              subgroup_name: "Work Pool",
              user_id: 9,
              username: "bob",
              created_at: "2026-06-01T12:00:00Z",
            },
          ],
        });
      }
      if (url.includes("/subgroups/mine")) return Promise.resolve({ data: [] });
      if (url.includes("/subgroups/directory")) return Promise.resolve({ data: [] });
      if (url.includes("/subgroups/invites/pending")) return Promise.resolve({ data: [] });
      return Promise.resolve({ data: [] });
    });

    renderWithProviders(<Subgroups />);

    await waitFor(() => {
      expect(screen.getByText(/bob/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /approve/i }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/subgroups/4/join-requests/12/approve");
    });
  });
});
