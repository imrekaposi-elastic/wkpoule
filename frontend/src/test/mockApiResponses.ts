import type { Mock } from "vitest";

type ApiMock = {
  get: Mock;
  post: Mock;
  patch: Mock;
  delete: Mock;
};

export function mockApiResponses(api: ApiMock) {
  api.get.mockImplementation((url: string) => {
    if (url.includes("/rankings/me")) {
      return Promise.resolve({
        data: {
          rank: 2,
          user_id: 1,
          username: "alice",
          total_points: 15,
          correct_results: 1,
          correct_scores: 0,
          correct_goal_counts: 1,
          predictions_made: 3,
        },
      });
    }
    if (url.includes("next-needing-prediction")) {
      return Promise.resolve({ data: null });
    }
    if (url.includes("/subgroups/mine")) {
      return Promise.resolve({ data: [] });
    }
    if (url.includes("/subgroups/directory")) {
      return Promise.resolve({ data: [] });
    }
    if (url.includes("/subgroups/invites/pending")) {
      return Promise.resolve({ data: [] });
    }
    if (url.includes("/subgroups/join-requests/incoming")) {
      return Promise.resolve({ data: [] });
    }
    if (url.includes("/admin/subgroups")) {
      return Promise.resolve({ data: [] });
    }
    if (url.includes("/predictions/mine/brief")) {
      return Promise.resolve({ data: [] });
    }
    if (url.includes("/predictions/virtual-groups")) {
      return Promise.resolve({ data: [] });
    }
    if (url.includes("/matches/by-day")) {
      return Promise.resolve({ data: [] });
    }
    if (url.includes("/matches/calendar-meta")) {
      return Promise.resolve({
        data: {
          first_kickoff_utc: "2026-06-11T18:00:00Z",
          first_match_local_date: "2026-06-11",
        },
      });
    }
    if (url.includes("/matches")) {
      return Promise.resolve({
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 1,
        },
      });
    }
    return Promise.resolve({ data: [] });
  });
  api.post.mockResolvedValue({ data: {} });
  api.patch.mockResolvedValue({ data: {} });
  api.delete.mockResolvedValue({ data: {} });
}
