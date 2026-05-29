import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import ExpertAvatar from "../components/ExpertAvatar";
import Pagination from "../components/Pagination";
import VirtualGroupStandings from "../components/VirtualGroupStandings";
import { resolveLocale } from "../i18n/languages";
import { localizedTeam } from "../i18n/teamNames";
import { formatStageSlug } from "../utils/formatStage";
import { funCommentText } from "../utils/funCommentText";
import { isKnockoutStage, isPredictedDraw } from "../utils/predictions";
import type { Match, MyPredictionBrief, PaginatedResponse, Prediction, VirtualGroupTable } from "../types";

const PREDICTION_TIP_STORAGE_KEY = "wkpoule_prediction_progress_tip_dismissed";

type ScoreInput = number | "";

function readPredictionTipDismissed(): boolean {
  try {
    return localStorage.getItem(PREDICTION_TIP_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

function parseScoreField(raw: string): ScoreInput {
  if (raw === "") return "";
  const n = Number(raw);
  if (Number.isNaN(n)) return "";
  return Math.min(20, Math.max(0, Math.trunc(n)));
}

export default function MatchDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const [match, setMatch] = useState<Match | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [predPage, setPredPage] = useState(1);
  const [predTotalPages, setPredTotalPages] = useState(1);
  const [predTotal, setPredTotal] = useState(0);
  const [homeScore, setHomeScore] = useState<ScoreInput>("");
  const [awayScore, setAwayScore] = useState<ScoreInput>("");
  const [advanceTeamId, setAdvanceTeamId] = useState<number | null>(null);
  const [predictionTipDismissed, setPredictionTipDismissed] = useState(readPredictionTipDismissed);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [virtualStandings, setVirtualStandings] = useState<VirtualGroupTable | null>(null);
  const [virtualLoading, setVirtualLoading] = useState(false);

  const locale = resolveLocale(i18n.language);

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
    setHomeScore("");
    setAwayScore("");
    setAdvanceTeamId(null);
    setVirtualStandings(null);

    const applyMyScoresFromBrief = async (matchId: number) => {
      try {
        const briefRes = await api.get<MyPredictionBrief[]>("/predictions/mine/brief");
        const myPred = briefRes.data.find((b) => b.match_id === matchId);
        if (myPred) {
          setHomeScore(myPred.home_score);
          setAwayScore(myPred.away_score);
          setAdvanceTeamId(myPred.advance_team_id ?? null);
        } else {
          setHomeScore("");
          setAwayScore("");
          setAdvanceTeamId(null);
        }
      } catch {
        setHomeScore("");
        setAwayScore("");
        setAdvanceTeamId(null);
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

        if (!cancelled) {
          await applyMyScoresFromBrief(matchRes.data.id);
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
    if (!match?.id || predPage < 1) return;
    let cancelled = false;
    api
      .get<PaginatedResponse<Prediction>>(`/predictions/match/${match.id}`, {
        params: { page: predPage, page_size: 20 },
      })
      .then((r) => {
        if (cancelled) return;
        setPredictions(r.data.items);
        setPredTotalPages(r.data.total_pages);
        setPredTotal(r.data.total);
      })
      .catch(() => {
        if (!cancelled) setPredictions([]);
      });
    return () => {
      cancelled = true;
    };
  }, [match?.id, predPage]);

  useEffect(() => {
    setPredPage(1);
  }, [match?.id]);

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
      if (homeScore === "" || awayScore === "") {
        setMessage(t("matchDetail.scoresRequired"));
        return;
      }
      const knockoutDraw =
        isKnockoutStage(match.stage) &&
        isPredictedDraw(homeScore, awayScore) &&
        match.home_team &&
        match.away_team;
      if (knockoutDraw && advanceTeamId === null) {
        setMessage(t("matchDetail.advanceTeamRequired"));
        return;
      }
      await api.put(`/predictions/${match.id}`, {
        home_score: homeScore,
        away_score: awayScore,
        advance_team_id: knockoutDraw ? advanceTeamId : null,
      });
      await api.get<PaginatedResponse<Prediction>>(`/predictions/match/${match.id}`, {
        params: { page: predPage, page_size: 20 },
      }).then((r) => {
        setPredictions(r.data.items);
        setPredTotal(r.data.total);
        setPredTotalPages(r.data.total_pages);
      });

      if (match.group_letter) {
        await loadVirtualStandings(match.group_letter);
      }

      const nextRes = await api.get<Match | null>("/matches/next-needing-prediction", {
        params: { predicted_teams: "true" },
      });
      const nextEmpty = nextRes.data;

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
  const showKnockoutAfter90Hint = isKnockoutStage(match.stage);
  const showAdvancePicker =
    canEditPrediction &&
    isKnockoutStage(match.stage) &&
    isPredictedDraw(homeScore, awayScore) &&
    Boolean(match.home_team && match.away_team);
  const advanceTeamLabel = (teamId: number | null | undefined) => {
    if (!teamId || !match.home_team || !match.away_team) return null;
    if (teamId === match.home_team.id) return localizedTeam(match.home_team, i18n.language);
    if (teamId === match.away_team.id) return localizedTeam(match.away_team, i18n.language);
    return null;
  };
  const readOnlyPredictionBoxClass =
    "rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 opacity-90";
  const readOnlyPredictionScoreClass =
    "text-2xl font-bold font-mono text-gray-400 tabular-nums";

  const successMessages = [t("matchDetail.saved"), t("matchDetail.savedAllComplete")];
  const isSuccessMessage = message !== "" && successMessages.includes(message);

  const commentText = (() => {
    if (!match.fun_comment) return null;
    if (i18n.language === "he") {
      const home = match.home_team ? localizedTeam(match.home_team, i18n.language) : t("matches.tbd");
      const away = match.away_team ? localizedTeam(match.away_team, i18n.language) : t("matches.tbd");
      return `${home} נגד ${away}: המומחה צופה משחק מסקרן שבו הדירוג, המומנטום והאווירה באצטדיון יכולים להשפיע על כל מהלך.`;
    }
    return funCommentText(match.fun_comment, i18n.language);
  })();

  return (
    <div className="max-w-4xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <div className="bg-white rounded-xl shadow-lg mb-6">
        <div className="bg-pitch-800 text-white px-4 sm:px-6 py-3 sm:py-4 rounded-t-xl">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between text-sm">
            <span>
              {t("matchDetail.match", { number: match.match_number })} &middot;{" "}
              {match.group_letter
                ? t("matches.group", { letter: match.group_letter })
                : formatStageSlug(match.stage)}
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

        <div className="p-4 sm:p-6 rounded-b-xl">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-5 sm:gap-6 md:gap-8 mb-6 w-full max-w-full min-w-0">
            <div className="text-center flex-1 min-w-0 sm:min-w-[7rem] px-1 order-1">
              {match.home_team ? (
                <>
                  <img src={match.home_team.flag_url} alt="" className="w-16 h-11 object-cover rounded mx-auto mb-2" />
                  <h2 className="font-bold text-base sm:text-lg break-words">
                    {localizedTeam(match.home_team, i18n.language)}
                  </h2>
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

            <div className="text-center order-2 py-1 sm:py-0 w-full max-w-full sm:w-auto shrink-0">
              {match.status === "completed" ? (
                <div className="text-3xl sm:text-4xl font-bold tabular-nums">
                  {match.home_score} - {match.away_score}
                </div>
              ) : (
                <div className="text-xl sm:text-2xl font-light text-gray-400">{t("matches.vs")}</div>
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

            <div className="text-center flex-1 min-w-0 sm:min-w-[7rem] px-1 order-3 w-full max-w-full">
              {match.away_team ? (
                <>
                  <img src={match.away_team.flag_url} alt="" className="w-16 h-11 object-cover rounded mx-auto mb-2" />
                  <h2 className="font-bold text-base sm:text-lg break-words">
                    {localizedTeam(match.away_team, i18n.language)}
                  </h2>
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

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 text-sm border-t pt-4">
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        <div className="space-y-6">
          {match.expert_prediction && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
                {t("matchDetail.expertPrediction")}
              </h3>
              <p className="text-lg font-semibold text-pitch-700">
                {match.expert_prediction.home_goals}-{match.expert_prediction.away_goals}
              </p>
            </div>
          )}

          {match.fun_comment && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="mb-3 flex items-center gap-3">
                <ExpertAvatar
                  styleKey={match.fun_comment.style}
                  label={t(`matchDetail.styles.${match.fun_comment.style}`, match.fun_comment.style)}
                  size="sm"
                />
                <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                  {t("matchDetail.expertCommentary")}
                  <span className="mt-1 block text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full normal-case w-fit">
                    {t(`matchDetail.styles.${match.fun_comment.style}`, match.fun_comment.style)}
                  </span>
                </h3>
              </div>
              <p className="text-gray-700 italic leading-relaxed">
                "{commentText}"
              </p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-md p-4 sm:p-6 min-w-0">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
            {t("matchDetail.yourPrediction")}
          </h3>
          {canEditPrediction ? (
            <form onSubmit={handleSubmit}>
              {showKnockoutAfter90Hint && (
                <p className="mb-4 text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 leading-relaxed">
                  {t("matchDetail.knockoutAfter90Hint")}
                </p>
              )}
              {!predictionTipDismissed && (
                <div className="mb-4 rounded-lg border border-sky-200 bg-sky-50 px-3 py-3 text-sm text-sky-950">
                  <p className="mb-3 leading-relaxed">{t("matchDetail.predictionProgressTip")}</p>
                  <label className="flex items-start gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="mt-0.5 rounded border-gray-300 text-pitch-600 focus:ring-pitch-500"
                      onChange={(e) => {
                        if (e.target.checked) {
                          try {
                            localStorage.setItem(PREDICTION_TIP_STORAGE_KEY, "1");
                          } catch {
                            /* ignore */
                          }
                          setPredictionTipDismissed(true);
                        }
                      }}
                    />
                    <span>{t("matchDetail.predictionTipAcknowledge")}</span>
                  </label>
                </div>
              )}
              <div className="grid grid-cols-[1fr_auto_1fr] items-end gap-2 sm:flex sm:flex-wrap sm:items-center sm:justify-center sm:gap-4 mb-4 w-full max-w-full min-w-0">
                <div className="text-center min-w-0">
                  <label className="block text-sm text-gray-600 mb-1 truncate">
                    {match.home_team?.fifa_code || t("matchDetail.home")}
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={20}
                    value={homeScore === "" ? "" : homeScore}
                    onChange={(e) => {
                      setHomeScore(parseScoreField(e.target.value));
                      const nextHome = parseScoreField(e.target.value);
                      const away = awayScore === "" ? "" : awayScore;
                      if (!isPredictedDraw(nextHome, away)) setAdvanceTeamId(null);
                    }}
                    className="w-full max-w-[5.5rem] mx-auto sm:w-20 text-center text-2xl font-bold border border-gray-300 rounded-lg py-2 focus:ring-2 focus:ring-pitch-600 outline-none"
                    inputMode="numeric"
                  />
                </div>
                <span className="text-gray-400 text-xl pb-2 sm:pb-0 sm:mt-6 self-center sm:self-auto">-</span>
                <div className="text-center min-w-0">
                  <label className="block text-sm text-gray-600 mb-1 truncate">
                    {match.away_team?.fifa_code || t("matchDetail.away")}
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={20}
                    value={awayScore === "" ? "" : awayScore}
                    onChange={(e) => {
                      setAwayScore(parseScoreField(e.target.value));
                      const nextAway = parseScoreField(e.target.value);
                      const home = homeScore === "" ? "" : homeScore;
                      if (!isPredictedDraw(home, nextAway)) setAdvanceTeamId(null);
                    }}
                    className="w-full max-w-[5.5rem] mx-auto sm:w-20 text-center text-2xl font-bold border border-gray-300 rounded-lg py-2 focus:ring-2 focus:ring-pitch-600 outline-none"
                    inputMode="numeric"
                  />
                </div>
              </div>
              {showAdvancePicker && match.home_team && match.away_team && (
                <fieldset className="mb-4 rounded-lg border border-pitch-200 bg-pitch-50/50 px-3 py-3">
                  <legend className="text-sm font-medium text-pitch-900 px-1">
                    {t("matchDetail.advanceTeamLegend")}
                  </legend>
                  <p className="text-xs text-gray-600 mb-3">{t("matchDetail.advanceTeamHelp")}</p>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <label
                      className={`flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer flex-1 ${
                        advanceTeamId === match.home_team.id
                          ? "border-pitch-600 bg-white ring-1 ring-pitch-600"
                          : "border-gray-200 bg-white hover:border-pitch-300"
                      }`}
                    >
                      <input
                        type="radio"
                        name="advanceTeam"
                        className="text-pitch-600 focus:ring-pitch-500"
                        checked={advanceTeamId === match.home_team.id}
                        onChange={() => setAdvanceTeamId(match.home_team!.id)}
                      />
                      <span className="text-sm font-medium truncate">
                        {localizedTeam(match.home_team, i18n.language)}
                      </span>
                    </label>
                    <label
                      className={`flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer flex-1 ${
                        advanceTeamId === match.away_team.id
                          ? "border-pitch-600 bg-white ring-1 ring-pitch-600"
                          : "border-gray-200 bg-white hover:border-pitch-300"
                      }`}
                    >
                      <input
                        type="radio"
                        name="advanceTeam"
                        className="text-pitch-600 focus:ring-pitch-500"
                        checked={advanceTeamId === match.away_team.id}
                        onChange={() => setAdvanceTeamId(match.away_team!.id)}
                      />
                      <span className="text-sm font-medium truncate">
                        {localizedTeam(match.away_team, i18n.language)}
                      </span>
                    </label>
                  </div>
                </fieldset>
              )}
              <button
                type="submit"
                disabled={
                  saving ||
                  homeScore === "" ||
                  awayScore === "" ||
                  (showAdvancePicker && advanceTeamId === null)
                }
                className="w-full bg-pitch-600 hover:bg-pitch-700 text-white py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {saving ? t("matchDetail.saving") : t("matchDetail.savePrediction")}
              </button>
              {message && (
                <p
                  className={`mt-2 text-sm text-center ${
                    isSuccessMessage ? "text-green-600" : "text-red-600"
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
                <div className={`${readOnlyPredictionBoxClass} space-y-2 text-center`}>
                  <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 pointer-events-none select-none">
                    <span className={readOnlyPredictionScoreClass}>{myPredRow.home_score}</span>
                    <span className="text-gray-300 text-xl">-</span>
                    <span className={readOnlyPredictionScoreClass}>{myPredRow.away_score}</span>
                  </div>
                  {myPredRow.home_score === myPredRow.away_score &&
                    advanceTeamLabel(myPredRow.advance_team_id) && (
                      <p className="text-xs text-gray-500">
                        {t("matchDetail.advanceTeamReadOnly", {
                          team: advanceTeamLabel(myPredRow.advance_team_id),
                        })}
                      </p>
                    )}
                </div>
              ) : (
                <p className="text-sm text-gray-400">{t("matchDetail.noPredictionBeforeLock")}</p>
              )}
            </div>
          ) : (
            <div className="text-center py-2 space-y-3">
              <p className="text-gray-500">{t("matchDetail.predictionReadOnly")}</p>
              {myPredRow ? (
                <div className={`${readOnlyPredictionBoxClass} space-y-2 text-center`}>
                  <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 pointer-events-none select-none">
                    <span className={readOnlyPredictionScoreClass}>{myPredRow.home_score}</span>
                    <span className="text-gray-300 text-xl">-</span>
                    <span className={readOnlyPredictionScoreClass}>{myPredRow.away_score}</span>
                  </div>
                  {myPredRow.home_score === myPredRow.away_score &&
                    advanceTeamLabel(myPredRow.advance_team_id) && (
                      <p className="text-xs text-gray-500">
                        {t("matchDetail.advanceTeamReadOnly", {
                          team: advanceTeamLabel(myPredRow.advance_team_id),
                        })}
                      </p>
                    )}
                </div>
              ) : (
                <p className="text-sm text-gray-400">{t("matchDetail.locked")}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {match.stage === "group" && match.group_letter && (
        <div className="mt-6">
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

      <div className="bg-white rounded-xl shadow-md p-6 mt-6">
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
          {t("matchDetail.allPredictions")} ({predTotal})
        </h3>
        {predictions.length === 0 ? (
          <p className="text-gray-500 text-center py-4">{t("matchDetail.noPredictions")}</p>
        ) : (
          <div className="overflow-x-auto overscroll-x-contain -mx-1">
            <table className="w-full text-sm min-w-[20rem]">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 font-medium">{t("matchDetail.user")}</th>
                  <th className="pb-2 font-medium text-center">{t("matchDetail.prediction")}</th>
                  <th className="pb-2 font-medium text-center">{t("rankings.points")}</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((p) => {
                  const isMe = p.user_id === user?.id;
                  const myRowReadOnly = isMe && !canEditPrediction;
                  return (
                  <tr
                    key={p.id}
                    className={`border-b last:border-0 ${
                      isMe
                        ? myRowReadOnly
                          ? "bg-gray-50 text-gray-500"
                          : "bg-green-50"
                        : ""
                    }`}
                  >
                    <td className="py-2.5">
                      {p.username}
                      {isMe && (
                        <span
                          className={`ml-1 text-xs ${
                            myRowReadOnly ? "text-gray-400" : "text-pitch-600"
                          }`}
                        >
                          {t("matchDetail.you")}
                        </span>
                      )}
                    </td>
                    <td
                      className={`py-2.5 text-center font-mono font-semibold ${
                        myRowReadOnly ? "text-gray-400" : ""
                      }`}
                    >
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
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          page={predPage}
          totalPages={predTotalPages}
          total={predTotal}
          onPageChange={setPredPage}
        />
      </div>
    </div>
  );
}
