import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import Pagination from "./Pagination";
import type {
  MatchPredictionListItem,
  MatchPredictionSummary,
  PaginatedResponse,
  Team,
} from "../types";
import { localizedTeam } from "../i18n/teamNames";

export type PredictionOutcome = "home_win" | "away_win" | "draw";

type Props = {
  matchId: number;
  homeTeam: Team | null | undefined;
  awayTeam: Team | null | undefined;
  refreshKey?: number;
};

function advanceLabel(
  advanceTeamId: number | null | undefined,
  homeTeam: Team | null | undefined,
  awayTeam: Team | null | undefined,
  language: string,
): string | null {
  if (!advanceTeamId || !homeTeam || !awayTeam) return null;
  if (advanceTeamId === homeTeam.id) return localizedTeam(homeTeam, language);
  if (advanceTeamId === awayTeam.id) return localizedTeam(awayTeam, language);
  return null;
}

export default function MatchPredictionsSummary({
  matchId,
  homeTeam,
  awayTeam,
  refreshKey = 0,
}: Props) {
  const { t, i18n } = useTranslation();
  const [summary, setSummary] = useState<MatchPredictionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalOutcome, setModalOutcome] = useState<PredictionOutcome | null>(null);
  const [modalPage, setModalPage] = useState(1);
  const [modalItems, setModalItems] = useState<MatchPredictionListItem[]>([]);
  const [modalTotalPages, setModalTotalPages] = useState(1);
  const [modalTotal, setModalTotal] = useState(0);
  const [modalLoading, setModalLoading] = useState(false);

  const homeName = homeTeam ? localizedTeam(homeTeam, i18n.language) : t("matchDetail.home");
  const awayName = awayTeam ? localizedTeam(awayTeam, i18n.language) : t("matchDetail.away");

  const outcomeLabel = (outcome: PredictionOutcome): string => {
    if (outcome === "home_win") {
      return t("matchDetail.teamWinPredicted", { team: homeName });
    }
    if (outcome === "away_win") {
      return t("matchDetail.teamWinPredicted", { team: awayName });
    }
    return t("matchDetail.drawPredicted");
  };

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .get<MatchPredictionSummary>(`/predictions/match/${matchId}/summary`)
      .then((r) => {
        if (!cancelled) setSummary(r.data);
      })
      .catch(() => {
        if (!cancelled) setSummary(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [matchId, refreshKey]);

  const loadModalPage = useCallback(
    (outcome: PredictionOutcome, page: number) => {
      setModalLoading(true);
      api
        .get<PaginatedResponse<MatchPredictionListItem>>(
          `/predictions/match/${matchId}/by-outcome`,
          { params: { outcome, page, page_size: 10 } },
        )
        .then((r) => {
          setModalItems(r.data.items);
          setModalTotalPages(r.data.total_pages);
          setModalTotal(r.data.total);
        })
        .catch(() => {
          setModalItems([]);
          setModalTotalPages(1);
          setModalTotal(0);
        })
        .finally(() => setModalLoading(false));
    },
    [matchId],
  );

  useEffect(() => {
    if (!modalOutcome) return;
    loadModalPage(modalOutcome, modalPage);
  }, [modalOutcome, modalPage, loadModalPage]);

  const openOutcome = (outcome: PredictionOutcome) => {
    setModalOutcome(outcome);
    setModalPage(1);
  };

  const closeModal = () => {
    setModalOutcome(null);
    setModalItems([]);
  };

  const rows: { outcome: PredictionOutcome; count: number }[] = summary
    ? [
        { outcome: "home_win", count: summary.home_win_count },
        { outcome: "away_win", count: summary.away_win_count },
        { outcome: "draw", count: summary.draw_count },
      ]
    : [];

  return (
    <>
      <div className="bg-white rounded-xl shadow-md p-6 mt-6">
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
          {t("matchDetail.allPredictions")}
          {summary ? ` (${summary.total})` : ""}
        </h3>
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-pitch-600" />
          </div>
        ) : !summary || summary.total === 0 ? (
          <p className="text-gray-500 text-center py-4">{t("matchDetail.noPredictions")}</p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {rows.map(({ outcome, count }) => (
              <li
                key={outcome}
                className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"
              >
                <span className="text-sm text-gray-800">{outcomeLabel(outcome)}</span>
                {count > 0 ? (
                  <button
                    type="button"
                    onClick={() => openOutcome(outcome)}
                    className="min-w-[2.5rem] rounded-lg bg-pitch-50 px-3 py-1.5 text-sm font-semibold tabular-nums text-pitch-800 hover:bg-pitch-100 transition-colors touch-manipulation"
                    aria-label={t("matchDetail.viewOutcomePredictions", {
                      label: outcomeLabel(outcome),
                      count,
                    })}
                  >
                    {count}
                  </button>
                ) : (
                  <span className="min-w-[2.5rem] px-3 py-1.5 text-sm tabular-nums text-gray-400 text-center">
                    0
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {modalOutcome && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
          role="presentation"
          onClick={closeModal}
        >
          <div
            className="bg-white rounded-xl shadow-xl max-w-md w-full max-h-[90dvh] flex flex-col text-gray-900"
            role="dialog"
            aria-labelledby="outcome-predictions-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 pb-3 border-b border-gray-100 shrink-0">
              <h2 id="outcome-predictions-title" className="text-lg font-bold text-pitch-800">
                {t("matchDetail.outcomePopupTitle", { label: outcomeLabel(modalOutcome) })}
              </h2>
            </div>
            <div className="overflow-y-auto flex-1 px-6 py-3">
              {modalLoading ? (
                <div className="flex justify-center py-10">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pitch-600" />
                </div>
              ) : modalItems.length === 0 ? (
                <p className="text-gray-500 text-center py-6">{t("matchDetail.noPredictions")}</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="pb-2 font-medium">{t("matchDetail.user")}</th>
                      <th className="pb-2 font-medium text-center">{t("matchDetail.prediction")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {modalItems.map((p) => {
                      const adv = advanceLabel(
                        p.advance_team_id,
                        homeTeam,
                        awayTeam,
                        i18n.language,
                      );
                      return (
                        <tr key={p.user_id} className="border-b last:border-0">
                          <td className="py-2.5">{p.username}</td>
                          <td className="py-2.5 text-center">
                            <span className="font-mono font-semibold tabular-nums">
                              {p.home_score} - {p.away_score}
                            </span>
                            {adv && (
                              <span className="block text-xs text-gray-500 mt-0.5">
                                {t("matchDetail.advanceTeamReadOnly", { team: adv })}
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
            <div className="px-6 pt-0 pb-4 shrink-0">
              <Pagination
                page={modalPage}
                totalPages={modalTotalPages}
                total={modalTotal}
                onPageChange={setModalPage}
                disabled={modalLoading}
              />
              <button
                type="button"
                onClick={closeModal}
                className="mt-2 w-full sm:w-auto text-sm bg-pitch-700 hover:bg-pitch-800 text-white px-4 py-2 rounded-md transition-colors touch-manipulation min-h-[44px]"
              >
                {t("helpAbout.close")}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
