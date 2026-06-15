import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { beforeAuthenticatedPoll } from "../api/authenticatedPoll";
import MatchDayCalendar from "../components/MatchDayCalendar";
import { useAuth } from "../context/AuthContext";
import { resolveLocale } from "../i18n/languages";
import type {
  Match,
  ParticipantRanking,
  SubgroupDetail,
  SubgroupMine,
} from "../types";
import { rankingsItems } from "../utils/rankings";

const TOTAL_PREDICTIONS = 104;

export default function Dashboard() {
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const [matchToPredict, setMatchToPredict] = useState<Match | null>(null);
  const [myRank, setMyRank] = useState<ParticipantRanking | null>(null);
  const [subgroupMine, setSubgroupMine] = useState<SubgroupMine[]>([]);
  const [subgroupRankings, setSubgroupRankings] = useState<SubgroupDetail[]>([]);
  const [loading, setLoading] = useState(true);

  const locale = resolveLocale(i18n.language);
  const predictionsMade = myRank?.predictions_made || 0;
  const predictionsComplete = predictionsMade >= TOTAL_PREDICTIONS;

  const loadSubgroupRankings = useCallback((mine: SubgroupMine[]) => {
    if (mine.length === 0) {
      setSubgroupRankings([]);
      return Promise.resolve();
    }
    return Promise.all(
      mine.map((s) =>
        api
          .get<SubgroupDetail>(`/subgroups/${s.id}`, {
            params: { page: 1, page_size: 20 },
          })
          .then((r) => r.data),
      ),
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
      api.get<Match | null>("/matches/next-needing-prediction", {
        params: { predicted_teams: "true" },
      }),
      api.get<ParticipantRanking | null>("/rankings/me"),
      api.get<SubgroupMine[]>("/subgroups/mine").catch(() => ({ data: [] as SubgroupMine[] })),
    ])
      .then(([nextRes, myRankRes, subRes]) => {
        setMatchToPredict(nextRes.data);
        setMyRank(myRankRes.data);
        setSubgroupMine(subRes.data);
        return loadSubgroupRankings(subRes.data);
      })
      .finally(() => setLoading(false));
  }, [user?.id, loadSubgroupRankings]);

  useEffect(() => {
    if (!user) return;
    const refreshMine = () => {
      void beforeAuthenticatedPoll().then((ok) => {
        if (!ok) return;
        api
          .get<SubgroupMine[]>("/subgroups/mine")
          .then((r) => {
            setSubgroupMine(r.data);
            loadSubgroupRankings(r.data);
          })
          .catch(() => {});
      });
    };
    const tmr = window.setInterval(refreshMine, 30000);
    window.addEventListener("subgroups-mine-changed", refreshMine);
    return () => {
      window.clearInterval(tmr);
      window.removeEventListener("subgroups-mine-changed", refreshMine);
    };
  }, [loadSubgroupRankings, user]);

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
              <span
                className={`font-semibold text-right ${
                  predictionsComplete ? "text-green-700" : "text-red-700"
                }`}
              >
                {predictionsComplete
                  ? t("dashboard.allPredictionsComplete")
                  : `${predictionsMade} / ${TOTAL_PREDICTIONS}`}
              </span>
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

        {/* Next match to predict */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
            {t("dashboard.nextToPredict")}
          </h2>
          {matchToPredict ? (
            <div className="mt-3">
              <p className="text-xs text-gray-500 mb-2">
                {t("dashboard.matchNumber", { number: matchToPredict.match_number })}
              </p>
              <div className="flex items-center gap-3">
                {matchToPredict.home_team ? (
                  <div className="flex items-center gap-1.5">
                    <img src={matchToPredict.home_team.flag_url} alt="" className="w-6 h-4 object-cover rounded-sm" />
                    <span className="font-semibold text-sm">{matchToPredict.home_team.fifa_code}</span>
                  </div>
                ) : (
                  <span className="text-sm text-gray-400">{t("dashboard.tbd")}</span>
                )}
                <span className="text-gray-400 text-xs">{t("dashboard.vs")}</span>
                {matchToPredict.away_team ? (
                  <div className="flex items-center gap-1.5">
                    <img src={matchToPredict.away_team.flag_url} alt="" className="w-6 h-4 object-cover rounded-sm" />
                    <span className="font-semibold text-sm">{matchToPredict.away_team.fifa_code}</span>
                  </div>
                ) : (
                  <span className="text-sm text-gray-400">{t("dashboard.tbd")}</span>
                )}
              </div>
              <p className="mt-2 text-sm text-gray-500">
                {new Date(matchToPredict.kickoff_utc).toLocaleDateString(locale, {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
              <p className="text-sm text-gray-500">{matchToPredict.venue.name}</p>
              <Link
                to={`/matches/${matchToPredict.match_number}`}
                className="mt-2 inline-block text-sm text-pitch-600 hover:underline font-medium"
              >
                {t("dashboard.makePrediction")}
              </Link>
            </div>
          ) : predictionsComplete ? (
            <p className="mt-3 text-green-700 text-sm font-medium">
              {t("dashboard.allPredictionsComplete")}
            </p>
          ) : (
            <p className="mt-3 text-gray-500">{t("dashboard.noMatchesToPredict")}</p>
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
                      {rankingsItems(sg.rankings).slice(0, 3).map((r) => (
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

      <MatchDayCalendar />
    </div>
  );
}
