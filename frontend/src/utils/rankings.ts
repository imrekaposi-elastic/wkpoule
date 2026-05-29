import type { PaginatedResponse, ParticipantRanking } from "../types";

/** API returns paginated rankings; older clients may still send/receive a plain array. */
export function rankingsItems(
  rankings: PaginatedResponse<ParticipantRanking> | ParticipantRanking[] | null | undefined,
): ParticipantRanking[] {
  if (!rankings) return [];
  if (Array.isArray(rankings)) return rankings;
  return Array.isArray(rankings.items) ? rankings.items : [];
}

export function normalizeRankingsResponse(
  data: PaginatedResponse<ParticipantRanking> | ParticipantRanking[],
): PaginatedResponse<ParticipantRanking> {
  if (Array.isArray(data)) {
    return {
      items: data,
      total: data.length,
      page: 1,
      page_size: data.length,
      total_pages: 1,
    };
  }
  return {
    items: data.items ?? [],
    total: data.total ?? 0,
    page: data.page ?? 1,
    page_size: data.page_size ?? 20,
    total_pages: data.total_pages ?? 1,
  };
}
