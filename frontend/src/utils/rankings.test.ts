import { describe, expect, it } from "vitest";

import type { PaginatedResponse, ParticipantRanking } from "../types";
import { normalizeRankingsResponse, rankingsItems } from "./rankings";

const ranking = (userId: number): ParticipantRanking => ({
  rank: userId,
  user_id: userId,
  username: `user${userId}`,
  total_points: userId * 10,
  correct_results: 1,
  correct_scores: 0,
  correct_goal_counts: 1,
  predictions_made: 2,
});

describe("rankingsItems", () => {
  it("returns empty list for nullish input", () => {
    expect(rankingsItems(null)).toEqual([]);
    expect(rankingsItems(undefined)).toEqual([]);
  });

  it("returns array input unchanged", () => {
    const rows = [ranking(1), ranking(2)];
    expect(rankingsItems(rows)).toEqual(rows);
  });

  it("returns paginated items when present", () => {
    const page: PaginatedResponse<ParticipantRanking> = {
      items: [ranking(3)],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    };
    expect(rankingsItems(page)).toEqual([ranking(3)]);
  });
});

describe("normalizeRankingsResponse", () => {
  it("wraps plain arrays", () => {
    const rows = [ranking(1), ranking(2)];
    expect(normalizeRankingsResponse(rows)).toEqual({
      items: rows,
      total: 2,
      page: 1,
      page_size: 2,
      total_pages: 1,
    });
  });

  it("fills defaults for sparse paginated payloads", () => {
    expect(
      normalizeRankingsResponse({
        items: [ranking(4)],
        total: undefined,
        page: undefined,
        page_size: undefined,
        total_pages: undefined,
      } as PaginatedResponse<ParticipantRanking>),
    ).toEqual({
      items: [ranking(4)],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 1,
    });
  });
});
