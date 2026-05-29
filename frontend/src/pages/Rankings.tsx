import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import Pagination from "../components/Pagination";
import { useAuth } from "../context/AuthContext";
import type { PaginatedResponse, ParticipantRanking } from "../types";

export default function Rankings() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [rankings, setRankings] = useState<ParticipantRanking[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback((p: number) => {
    setLoading(true);
    api
      .get<PaginatedResponse<ParticipantRanking>>("/rankings", {
        params: { page: p, page_size: 20 },
      })
      .then((r) => {
        setRankings(r.data.items);
        setPage(r.data.page);
        setTotalPages(r.data.total_pages);
        setTotal(r.data.total);
      })
      .catch(() => {
        setRankings([]);
        setTotal(0);
        setTotalPages(1);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load(page);
  }, [page, load]);

  if (loading && rankings.length === 0) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <h1 className="text-2xl sm:text-3xl font-bold mb-6 sm:mb-8">{t("rankings.title")}</h1>

      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto overscroll-x-contain -mx-px">
        <table className="w-full text-sm min-w-[36rem]">
          <thead>
            <tr className="bg-pitch-800 text-white">
              <th className="text-left py-3 px-4 font-medium w-16">{t("rankings.rank")}</th>
              <th className="text-left py-3 px-4 font-medium">{t("rankings.player")}</th>
              <th className="py-3 px-4 font-medium text-center">{t("rankings.predictions")}</th>
              <th className="py-3 px-4 font-medium text-center hidden sm:table-cell">
                {t("rankings.correctResults")}
              </th>
              <th className="py-3 px-4 font-medium text-center hidden sm:table-cell">
                {t("rankings.exactScores")}
              </th>
              <th className="py-3 px-4 font-medium text-center hidden md:table-cell">
                {t("rankings.goalCount")}
              </th>
              <th className="py-3 px-4 font-medium text-center">{t("rankings.points")}</th>
            </tr>
          </thead>
          <tbody>
            {rankings.map((r) => (
              <tr
                key={r.user_id}
                className={`border-b last:border-0 transition-colors ${
                  r.user_id === user?.id
                    ? "bg-green-50 font-semibold"
                    : "hover:bg-gray-50"
                }`}
              >
                <td className="py-3 px-4">
                  {r.rank <= 3 ? (
                    <span className="text-lg">
                      {r.rank === 1
                        ? "\uD83E\uDD47"
                        : r.rank === 2
                        ? "\uD83E\uDD48"
                        : "\uD83E\uDD49"}
                    </span>
                  ) : (
                    <span className="text-gray-500">{r.rank}</span>
                  )}
                </td>
                <td className="py-3 px-4">
                  {r.username}
                  {r.user_id === user?.id && (
                    <span className="ml-1 text-xs text-pitch-600">{t("rankings.you")}</span>
                  )}
                </td>
                <td className="py-3 px-4 text-center">{r.predictions_made}</td>
                <td className="py-3 px-4 text-center hidden sm:table-cell">{r.correct_results}</td>
                <td className="py-3 px-4 text-center hidden sm:table-cell">{r.correct_scores}</td>
                <td className="py-3 px-4 text-center hidden md:table-cell">{r.correct_goal_counts}</td>
                <td className="py-3 px-4 text-center">
                  <span className="text-lg font-bold text-pitch-700">{r.total_points}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>

        {rankings.length === 0 && !loading && (
          <p className="text-gray-500 text-center py-8">{t("rankings.noRankings")}</p>
        )}

        <Pagination
          page={page}
          totalPages={totalPages}
          total={total}
          onPageChange={setPage}
          disabled={loading}
        />
      </div>

      <div className="mt-6 bg-white rounded-xl shadow-md p-6">
        <h2 className="font-semibold mb-3">{t("rankings.scoringSystem")}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-pitch-700">3</div>
            <div className="text-gray-600">{t("rankings.correctResult")}</div>
            <div className="text-xs text-gray-400">{t("rankings.correctResultSub")}</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-pitch-700">8</div>
            <div className="text-gray-600">{t("rankings.exactScore")}</div>
            <div className="text-xs text-gray-400">{t("rankings.exactScoreSub")}</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-pitch-700">1</div>
            <div className="text-gray-600">{t("rankings.totalGoals")}</div>
            <div className="text-xs text-gray-400">{t("rankings.totalGoalsSub")}</div>
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-3 text-center">{t("rankings.cumulativeNote")}</p>
      </div>
    </div>
  );
}
