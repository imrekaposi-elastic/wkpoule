import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import { localizedTeamName } from "../i18n/teamNames";
import type {
  Match,
  MyPrediction,
  ParticipantRanking,
  SubgroupDetail,
  SubgroupMine,
} from "../types";

const LOCALE_MAP: Record<string, string> = {
  en: "en-US",
  nl: "nl-NL",
  pt: "pt-BR",
  de: "de-DE",
  he: "he-IL",
};

export default function Dashboard() {
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const [nextMatch, setNextMatch] = useState<Match | null>(null);
  const [myRank, setMyRank] = useState<ParticipantRanking | null>(null);
  const [recentPredictions, setRecentPredictions] = useState<MyPrediction[]>([]);
  const [subgroupMine, setSubgroupMine] = useState<SubgroupMine[]>([]);
  const [subgroupRankings, setSubgroupRankings] = useState<SubgroupDetail[]>([]);
  const [loading, setLoading] = useState(true);

  const locale = LOCALE_MAP[i18n.language] || "en-US";

  const loadSubgroupRankings = useCallback((mine: SubgroupMine[]) => {
    if (mine.length === 0) {
      setSubgroupRankings([]);
      return Promise.resolve();
    }
    return Promise.all(
      mine.map((s) => api.get<SubgroupDetail>(`/subgroups/${s.id}`).then((r) => r.data)),
    )
      .then((details) =>
        setSubgroupRankings(
          details.sort((a, b) =>
            a.name.localeCompare(b.name, undefined, { sensitivity: "base" }),
          ),
        ),
      )
      .catch(() => setSubgroupRankings([]));
  }, []);

  useEffect(() => {
    Promise.all([
      api.get<Match[]>("/matches", { params: { predicted_teams: "true" } }),
      api.get<ParticipantRanking[]>("/rankings"),
      api.get<MyPrediction[]>("/predictions/mine"),
      api.get<SubgroupMine[]>("/subgroups/mine").catch(() => ({ data: [] as SubgroupMine[] })),
    ])
      .then(([matchesRes, rankingsRes, predsRes, subRes]) => {
        const upcoming = matchesRes.data
          .filter((m) => m.status === "upcoming")
          .sort(
            (a, b) =>
              new Date(a.kickoff_utc).getTime() -
              new Date(b.kickoff_utc).getTime()
          );
        setNextMatch(upcoming[0] || null);
        const me = rankingsRes.data.find((r) => r.user_id === user?.id);
        setMyRank(me || null);
        setRecentPredictions(predsRes.data.slice(-5).reverse());
        setSubgroupMine(subRes.data);
        return loadSubgroupRankings(subRes.data);
      })
      .finally(() => setLoading(false));
  }, [user?.id, loadSubgroupRankings]);

  useEffect(() => {
    const refreshMine = () => {
      api
        .get<SubgroupMine[]>("/subgroups/mine")
        .then((r) => {
          setSubgroupMine(r.data);
          loadSubgroupRankings(r.data);
        })
        .catch(() => {});
    };
    const tmr = window.setInterval(refreshMine, 30000);
    window.addEventListener("subgroups-mine-changed", refreshMine);
    return () => {
      window.clearInterval(tmr);
      window.removeEventListener("subgroups-mine-changed", refreshMine);
    };
  }, [loadSubgroupRankings]);

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <h1 className="text-2xl sm:text-3xl font-bold mb-6 sm:mb-8 break-words">
        {t("dashboard.welcome", { name: user?.username })}
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
        {/* Rank Card */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
            {t("dashboard.yourRanking")}
          </h2>
          <p className="mt-2 text-4xl font-bold text-pitch-700">
            #{myRank?.rank || "-"}
          </p>
          <p className="mt-1 text-lg text-gray-600">
            {t("dashboard.points", { count: myRank?.total_points || 0 })}
          </p>
          <Link
            to="/rankings"
            className="mt-3 inline-block text-sm text-pitch-600 hover:underline"
          >
            {t("dashboard.viewLeaderboard")}
          </Link>
        </div>

        {/* Stats Card */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
            {t("dashboard.yourStats")}
          </h2>
          <div className="mt-3 space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">{t("dashboard.predictionsMade")}</span>
              <span className="font-semibold">{myRank?.predictions_made || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t("dashboard.correctResults")}</span>
              <span className="font-semibold">{myRank?.correct_results || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t("dashboard.exactScores")}</span>
              <span className="font-semibold">{myRank?.correct_scores || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t("dashboard.correctGoalCounts")}</span>
              <span className="font-semibold">{myRank?.correct_goal_counts || 0}</span>
            </div>
          </div>
        </div>

        {/* Next Match Card */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
            {t("dashboard.nextMatch")}
          </h2>
          {nextMatch ? (
            <div className="mt-3">
              <div className="flex items-center gap-3">
                {nextMatch.home_team && (
                  <div className="flex items-center gap-1.5">
                    <img src={nextMatch.home_team.flag_url} alt="" className="w-6 h-4 object-cover rounded-sm" />
                    <span className="font-semibold text-sm">{nextMatch.home_team.fifa_code}</span>
                  </div>
                )}
                <span className="text-gray-400 text-xs">{t("dashboard.vs")}</span>
                {nextMatch.away_team && (
                  <div className="flex items-center gap-1.5">
                    <img src={nextMatch.away_team.flag_url} alt="" className="w-6 h-4 object-cover rounded-sm" />
                    <span className="font-semibold text-sm">{nextMatch.away_team.fifa_code}</span>
                  </div>
                )}
              </div>
              <p className="mt-2 text-sm text-gray-500">
                {new Date(nextMatch.kickoff_utc).toLocaleDateString(locale, {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
              <p className="text-sm text-gray-500">{nextMatch.venue.name}</p>
              <Link
                to={`/matches/${nextMatch.match_number}`}
                className="mt-2 inline-block text-sm text-pitch-600 hover:underline"
              >
                {nextMatch.prediction_editable
                  ? t("dashboard.makePrediction")
                  : t("dashboard.viewMatch")}
              </Link>
            </div>
          ) : (
            <p className="mt-3 text-gray-500">{t("dashboard.noUpcoming")}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-start justify-between gap-3 mb-4">
            <h2 className="text-lg font-semibold text-pitch-900">
              {t("dashboard.subgroupRankingsTitle")}
            </h2>
            <Link
              to="/subgroups"
              className="text-sm text-pitch-600 hover:underline shrink-0"
            >
              {t("dashboard.viewSubgroups")}
            </Link>
          </div>
          {subgroupMine.length === 0 ? (
            <p className="text-sm text-gray-500">{t("dashboard.notInAnySubgroup")}</p>
          ) : subgroupRankings.length === 0 ? (
            <p className="text-sm text-gray-500">{t("dashboard.subgroupRankingsLoadFailed")}</p>
          ) : (
            <div className="grid sm:grid-cols-2 gap-4">
              {subgroupRankings.map((sg) => (
                <div
                  key={sg.id}
                  className="rounded-lg border border-gray-100 overflow-hidden"
                >
                  <div className="bg-pitch-800 text-white px-3 py-2 text-sm font-semibold flex items-center justify-between gap-2">
                    <span className="truncate">{sg.name}</span>
                    <Link
                      to={`/subgroups/${sg.id}`}
                      className="text-green-100 hover:text-white text-xs font-normal shrink-0"
                    >
                      {t("dashboard.openSubgroup")}
                    </Link>
                  </div>
                  <div className="overflow-x-auto overscroll-x-contain">
                  <table className="w-full text-sm min-w-[16rem]">
                    <thead>
                      <tr className="text-left text-gray-500 border-b bg-gray-50">
                        <th className="py-1.5 px-2 font-medium w-8">{t("rankings.rank")}</th>
                        <th className="py-1.5 px-2 font-medium">{t("rankings.player")}</th>
                        <th className="py-1.5 px-2 font-medium text-right w-14">
                          {t("rankings.points")}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {sg.rankings.slice(0, 3).map((r) => (
                        <tr
                          key={r.user_id}
                          className={`border-b last:border-0 ${
                            r.user_id === user?.id ? "bg-green-50 font-semibold" : ""
                          }`}
                        >
                          <td className="py-1.5 px-2 text-gray-600">{r.rank}</td>
                          <td className="py-1.5 px-2">
                            {r.username}
                            {r.user_id === user?.id && (
                              <span className="ml-1 text-xs text-pitch-600">
                                {t("rankings.you")}
                              </span>
                            )}
                          </td>
                          <td className="py-1.5 px-2 text-right font-bold text-pitch-700">
                            {r.total_points}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-start justify-between gap-3 mb-4">
            <h2 className="text-lg font-semibold text-pitch-900">
              {t("dashboard.unreadSubgroupTitle")}
            </h2>
            <Link
              to="/subgroups"
              className="text-sm text-pitch-600 hover:underline shrink-0"
            >
              {t("dashboard.viewSubgroups")}
            </Link>
          </div>
          {subgroupMine.filter((s) => (s.unread_message_count ?? 0) > 0).length === 0 ? (
            <p className="text-sm text-gray-500">{t("dashboard.noUnreadSubgroup")}</p>
          ) : (
            <ul className="space-y-2">
              {subgroupMine
                .filter((s) => (s.unread_message_count ?? 0) > 0)
                .map((s) => (
                  <li key={s.id}>
                    <Link
                      to={`/subgroups/${s.id}`}
                      className="flex items-center justify-between gap-3 rounded-lg border border-gray-100 px-3 py-2.5 hover:border-pitch-300 transition-colors"
                    >
                      <span className="font-medium text-pitch-900">{s.name}</span>
                      <span className="shrink-0 min-w-[1.35rem] h-6 px-1.5 flex items-center justify-center rounded-full bg-sky-600 text-white text-xs font-bold">
                        {(s.unread_message_count ?? 0) > 99
                          ? "99+"
                          : s.unread_message_count}
                      </span>
                    </Link>
                  </li>
                ))}
            </ul>
          )}
        </div>
      </div>

      {/* Recent Predictions */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-lg font-semibold mb-4">{t("dashboard.recentPredictions")}</h2>
        {recentPredictions.length === 0 ? (
          <p className="text-gray-500">
            {t("dashboard.noPredictions")}{" "}
            <Link to="/matches" className="text-pitch-600 hover:underline">
              {t("dashboard.startPredicting")}
            </Link>
          </p>
        ) : (
          <div className="overflow-x-auto overscroll-x-contain">
            <table className="w-full text-sm min-w-[28rem]">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 font-medium">#</th>
                  <th className="pb-2 font-medium">{t("dashboard.matchCol")}</th>
                  <th className="pb-2 font-medium">{t("dashboard.yourPrediction")}</th>
                  <th className="pb-2 font-medium">{t("dashboard.statusCol")}</th>
                  <th className="pb-2 font-medium">{t("dashboard.pointsCol")}</th>
                </tr>
              </thead>
              <tbody>
                {recentPredictions.map((p) => (
                  <tr key={p.match_id} className="border-b last:border-0">
                    <td className="py-2.5">{p.match_number}</td>
                    <td className="py-2.5">
                      {p.home_team
                        ? localizedTeamName(p.home_team_code, p.home_team, i18n.language)
                        : t("dashboard.tbd")}{" "}
                      vs{" "}
                      {p.away_team
                        ? localizedTeamName(p.away_team_code, p.away_team, i18n.language)
                        : t("dashboard.tbd")}
                    </td>
                    <td className="py-2.5 font-mono">
                      {p.home_score} - {p.away_score}
                    </td>
                    <td className="py-2.5">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                          p.match_status === "completed"
                            ? "bg-green-100 text-green-700"
                            : p.match_status === "in_progress"
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-blue-100 text-blue-700"
                        }`}
                      >
                        {t(`matches.${p.match_status}`, p.match_status)}
                      </span>
                    </td>
                    <td className="py-2.5 font-semibold">
                      {p.points !== null ? p.points : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
