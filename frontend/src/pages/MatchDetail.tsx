import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import VirtualGroupStandings from "../components/VirtualGroupStandings";
import type { Match, MyPrediction, Prediction, VirtualGroupTable } from "../types";

const LOCALE_MAP: Record<string, string> = {
  en: "en-US",
  nl: "nl-NL",
  pt: "pt-BR",
  de: "de-DE",
  he: "he-IL",
};

export default function MatchDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const [match, setMatch] = useState<Match | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [homeScore, setHomeScore] = useState(0);
  const [awayScore, setAwayScore] = useState(0);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [virtualStandings, setVirtualStandings] = useState<VirtualGroupTable | null>(null);
  const [virtualLoading, setVirtualLoading] = useState(false);

  const locale = LOCALE_MAP[i18n.language] || "en-US";

  const loadVirtualStandings = (
    groupLetter: string | null | undefined
  ): Promise<void> => {
    if (!groupLetter) {
      setVirtualStandings(null);
      setVirtualLoading(false);
      return Promise.resolve();
    }
    setVirtualLoading(true);
    return api
      .get<VirtualGroupTable[]>("/predictions/virtual-groups", {
        params: { _t: Date.now() },
      })
      .then((vr) => {
        const letter = groupLetter.trim().toUpperCase();
        const v =
          vr.data.find((x) => x.group_letter === letter) ??
          vr.data.find((x) => x.group_letter?.toUpperCase() === letter);
        setVirtualStandings(v ?? null);
      })
      .finally(() => setVirtualLoading(false));
  };

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    setHomeScore(0);
    setAwayScore(0);
    setVirtualStandings(null);

    const applyPredScores = (rows: Prediction[]) => {
      const myPred = rows.find((p) => p.user_id === user?.id);
      if (myPred) {
        setHomeScore(myPred.home_score);
        setAwayScore(myPred.away_score);
      }
    };

    (async () => {
      try {
        let matchRes;
        try {
          matchRes = await api.get<Match>(`/matches/by-number/${id}`, {
            params: { predicted_teams: "true" },
          });
        } catch (err: any) {
          if (err.response?.status === 404) {
            matchRes = await api.get<Match>(`/matches/${id}`, {
              params: { predicted_teams: "true" },
            });
          } else {
            throw err;
          }
        }
        if (cancelled) return;
        setMatch(matchRes.data);

        try {
          const predRes = await api.get<Prediction[]>(`/predictions/match/${matchRes.data.id}`);
          if (cancelled) return;
          setPredictions(predRes.data);
          applyPredScores(predRes.data);
        } catch {
          if (!cancelled) {
            setPredictions([]);
            setHomeScore(0);
            setAwayScore(0);
          }
        }
      } catch {
        if (!cancelled) setMatch(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [id, user?.id]);

  useEffect(() => {
    if (!match?.group_letter) {
      setVirtualStandings(null);
      return;
    }
    loadVirtualStandings(match.group_letter);
    // Include match.id so moving to another fixture in the *same* group refetches
    // (group_letter alone does not change when auto-advancing within the group).
  }, [match?.group_letter, match?.id]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      if (!match) return;
      await api.put(`/predictions/${match.id}`, {
        home_score: homeScore,
        away_score: awayScore,
      });
      const predRes = await api.get<Prediction[]>(`/predictions/match/${match.id}`);
      setPredictions(predRes.data);

      if (match.group_letter) {
        await loadVirtualStandings(match.group_letter);
      }

      const mineRes = await api.get<MyPrediction[]>("/predictions/mine");
      const predictedIds = new Set(mineRes.data.map((p) => p.match_id));
      const allMatches = await api.get<Match[]>("/matches", {
        params: { predicted_teams: "true" },
      });
      const nextEmpty = allMatches.data
        .filter((m) => m.status === "upcoming" && m.prediction_editable)
        .sort((a, b) => a.match_number - b.match_number)
        .find((m) => !predictedIds.has(m.id));

      if (nextEmpty && nextEmpty.match_number !== match.match_number) {
        navigate(`/matches/${nextEmpty.match_number}`, { replace: true });
        return;
      }
      setMessage(
        !nextEmpty ? t("matchDetail.savedAllComplete") : t("matchDetail.saved")
      );
    } catch (err: any) {
      setMessage(err.response?.data?.detail || t("matchDetail.saveFailed"));
    } finally {
      setSaving(false);
    }
  };

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );

  if (!match) return <div className="text-center py-20">{t("matchDetail.notFound")}</div>;

  const kickoff = new Date(match.kickoff_utc);
  const canEditPrediction =
    match.status === "upcoming" && match.prediction_editable;
  const myPredRow = predictions.find((p) => p.user_id === user?.id);

  const commentText = (() => {
    if (!match.fun_comment) return null;
    const fc = match.fun_comment as any;
    const langField = `comment_text_${i18n.language}`;
    return fc[langField] || fc.comment_text;
  })();

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-white rounded-xl shadow-lg overflow-hidden mb-6">
        <div className="bg-pitch-800 text-white px-6 py-4">
          <div className="flex items-center justify-between text-sm">
            <span>
              {t("matchDetail.match", { number: match.match_number })} &middot;{" "}
              {match.group_letter
                ? t("matches.group", { letter: match.group_letter })
                : match.stage.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </span>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                match.status === "completed"
                  ? "bg-green-500"
                  : match.status === "in_progress"
                  ? "bg-yellow-500 text-black"
                  : "bg-blue-500"
              }`}
            >
              {t(`matches.${match.status}`, match.status)}
            </span>
          </div>
        </div>

        <div className="p-6">
          <div className="flex items-center justify-center gap-8 mb-6">
            <div className="text-center flex-1">
              {match.home_team ? (
                <>
                  <img src={match.home_team.flag_url} alt="" className="w-16 h-11 object-cover rounded mx-auto mb-2" />
                  <h2 className="font-bold text-lg">{match.home_team.name}</h2>
                  {match.bracket_home_slot && (
                    <p className="text-xs font-mono text-gray-600 mb-1">{match.bracket_home_slot}</p>
                  )}
                  <p className="text-xs text-gray-500">
                    {t("matchDetail.fifaRanking")}: #{match.home_team.world_ranking}
                  </p>
                </>
              ) : (
                <>
                  <h2 className="font-bold text-lg text-gray-400">{t("matches.tbd")}</h2>
                  {match.bracket_home_slot && (
                    <p className="text-xs font-mono text-gray-600 mt-1">{match.bracket_home_slot}</p>
                  )}
                </>
              )}
            </div>

            <div className="text-center">
              {match.status === "completed" ? (
                <div className="text-4xl font-bold">
                  {match.home_score} - {match.away_score}
                </div>
              ) : (
                <div className="text-2xl font-light text-gray-400">{t("matches.vs")}</div>
              )}
              {(match.bracket_home_slot || match.bracket_away_slot) &&
                match.match_number >= 73 && (
                  <p className="text-xs font-mono text-gray-700 mt-2">
                    {[match.bracket_home_slot ?? "?", match.bracket_away_slot ?? "?"].join(" vs ")}
                  </p>
                )}
              <p className="text-sm text-gray-500 mt-1">
                {kickoff.toLocaleDateString(locale, {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                })}
              </p>
              <p className="text-sm text-gray-500">
                {kickoff.toLocaleTimeString(locale, {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>

            <div className="text-center flex-1">
              {match.away_team ? (
                <>
                  <img src={match.away_team.flag_url} alt="" className="w-16 h-11 object-cover rounded mx-auto mb-2" />
                  <h2 className="font-bold text-lg">{match.away_team.name}</h2>
                  {match.bracket_away_slot && (
                    <p className="text-xs font-mono text-gray-600 mb-1">{match.bracket_away_slot}</p>
                  )}
                  <p className="text-xs text-gray-500">
                    {t("matchDetail.fifaRanking")}: #{match.away_team.world_ranking}
                  </p>
                </>
              ) : (
                <>
                  <h2 className="font-bold text-lg text-gray-400">{t("matches.tbd")}</h2>
                  {match.bracket_away_slot && (
                    <p className="text-xs font-mono text-gray-600 mt-1">{match.bracket_away_slot}</p>
                  )}
                </>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm border-t pt-4">
            <div>
              <span className="text-gray-500 block">{t("matchDetail.venue")}</span>
              <span className="font-medium">{match.venue.name}</span>
            </div>
            <div>
              <span className="text-gray-500 block">{t("matchDetail.city")}</span>
              <span className="font-medium">
                {match.venue.city}, {match.venue.country}
              </span>
            </div>
            <div>
              <span className="text-gray-500 block">{t("matchDetail.capacity")}</span>
              <span className="font-medium">{match.venue.capacity.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-500 block">{t("matchDetail.temperature")}</span>
              <span className="font-medium">
                {match.temperature_celsius !== null
                  ? `${match.temperature_celsius}°C`
                  : t("matchDetail.na")}
              </span>
            </div>
          </div>
        </div>
      </div>

      {match.stage === "group" && match.group_letter && (
        <div className="mb-6">
          {virtualLoading && (
            <div className="flex justify-center py-8 bg-white rounded-xl shadow border border-gray-100">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-pitch-600" />
            </div>
          )}
          {!virtualLoading && virtualStandings && (
            <VirtualGroupStandings
              virtualGroup={virtualStandings}
              groupLetter={match.group_letter}
            />
          )}
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-6">
          {match.expert_prediction && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
                {t("matchDetail.expertPrediction")}
              </h3>
              <p className="text-lg font-semibold text-pitch-700">
                {match.expert_prediction.label}
              </p>
            </div>
          )}

          {match.fun_comment && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
                {t("matchDetail.expertCommentary")}
                <span className="ml-2 text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full normal-case">
                  {t(`matchDetail.styles.${match.fun_comment.style}`, match.fun_comment.style)}
                </span>
              </h3>
              <p className="text-gray-700 italic leading-relaxed">
                "{commentText}"
              </p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
            {t("matchDetail.yourPrediction")}
          </h3>
          {canEditPrediction ? (
            <form onSubmit={handleSubmit}>
              <div className="flex items-center justify-center gap-4 mb-4">
                <div className="text-center">
                  <label className="block text-sm text-gray-600 mb-1">
                    {match.home_team?.fifa_code || t("matchDetail.home")}
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={20}
                    value={homeScore}
                    onChange={(e) => setHomeScore(Number(e.target.value))}
                    className="w-20 text-center text-2xl font-bold border border-gray-300 rounded-lg py-2 focus:ring-2 focus:ring-pitch-600 outline-none"
                  />
                </div>
                <span className="text-gray-400 text-xl mt-6">-</span>
                <div className="text-center">
                  <label className="block text-sm text-gray-600 mb-1">
                    {match.away_team?.fifa_code || t("matchDetail.away")}
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={20}
                    value={awayScore}
                    onChange={(e) => setAwayScore(Number(e.target.value))}
                    className="w-20 text-center text-2xl font-bold border border-gray-300 rounded-lg py-2 focus:ring-2 focus:ring-pitch-600 outline-none"
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={saving}
                className="w-full bg-pitch-600 hover:bg-pitch-700 text-white py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {saving ? t("matchDetail.saving") : t("matchDetail.savePrediction")}
              </button>
              {message && (
                <p
                  className={`mt-2 text-sm text-center ${
                    message === t("matchDetail.saved") ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {message}
                </p>
              )}
            </form>
          ) : match.status === "upcoming" ? (
            <div className="text-center py-2 space-y-3">
              <p className="text-gray-500">{t("matchDetail.lockedBeforeKickoff")}</p>
              {myPredRow ? (
                <div className="flex items-center justify-center gap-4 text-2xl font-bold font-mono text-gray-800">
                  <span>{myPredRow.home_score}</span>
                  <span className="text-gray-400">-</span>
                  <span>{myPredRow.away_score}</span>
                </div>
              ) : (
                <p className="text-sm text-gray-400">{t("matchDetail.noPredictionBeforeLock")}</p>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">{t("matchDetail.locked")}</p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-md p-6 mt-6">
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
          {t("matchDetail.allPredictions")} ({predictions.length})
        </h3>
        {predictions.length === 0 ? (
          <p className="text-gray-500 text-center py-4">{t("matchDetail.noPredictions")}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 font-medium">{t("matchDetail.user")}</th>
                  <th className="pb-2 font-medium text-center">{t("matchDetail.prediction")}</th>
                  <th className="pb-2 font-medium text-center">{t("rankings.points")}</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((p) => (
                  <tr
                    key={p.id}
                    className={`border-b last:border-0 ${
                      p.user_id === user?.id ? "bg-green-50" : ""
                    }`}
                  >
                    <td className="py-2.5">
                      {p.username}
                      {p.user_id === user?.id && (
                        <span className="ml-1 text-xs text-pitch-600">{t("matchDetail.you")}</span>
                      )}
                    </td>
                    <td className="py-2.5 text-center font-mono font-semibold">
                      {p.home_score} - {p.away_score}
                    </td>
                    <td className="py-2.5 text-center font-semibold">
                      {p.points !== null ? (
                        <span className={p.points > 0 ? "text-green-600" : "text-gray-400"}>
                          {p.points}
                        </span>
                      ) : (
                        "-"
                      )}
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
