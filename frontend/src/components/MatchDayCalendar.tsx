import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { resolveLocale } from "../i18n/languages";
import { localizedTeam } from "../i18n/teamNames";
import type { Match, MyPredictionBrief, PaginatedResponse } from "../types";
import { formatStageSlug } from "../utils/formatStage";
import {
  browserTimeZone,
  compareLocalDateKeys,
  daysUntilLocalDate,
  formatCalendarDayHeader,
  formatMatchTime,
  formatTimeZoneLabel,
  kickoffToLocalDateKey,
  shiftLocalDateKey,
  todayLocalDateKey,
} from "../utils/matchCalendar";

interface CalendarMeta {
  first_kickoff_utc: string;
  first_match_local_date: string;
}

function predictionsByMatchId(mine: MyPredictionBrief[]) {
  const map: Record<number, { home: number; away: number }> = {};
  for (const p of mine) {
    map[p.match_id] = { home: p.home_score, away: p.away_score };
  }
  return map;
}

export default function MatchDayCalendar() {
  const { t, i18n } = useTranslation();
  const locale = resolveLocale(i18n.language);
  const timeZone = browserTimeZone();
  const [selectedDate, setSelectedDate] = useState(() => todayLocalDateKey());
  const [firstMatchLocalDate, setFirstMatchLocalDate] = useState<string | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [myPredByMatchId, setMyPredByMatchId] = useState<
    Record<number, { home: number; away: number }>
  >({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadFirstMatchDate() {
      try {
        const meta = await api.get<CalendarMeta>("/matches/calendar-meta", {
          params: { tz: timeZone },
        });
        if (!cancelled) {
          setFirstMatchLocalDate(meta.data.first_match_local_date);
        }
        return;
      } catch {
        // Fall back when calendar-meta is unavailable on older deployments.
      }

      try {
        const schedule = await api.get<PaginatedResponse<Match>>("/matches", {
          params: { page: 1, page_size: 1 },
        });
        const first = schedule.data.items[0];
        if (!cancelled && first) {
          setFirstMatchLocalDate(kickoffToLocalDateKey(first.kickoff_utc, timeZone));
        }
      } catch {
        if (!cancelled) setFirstMatchLocalDate(null);
      }
    }

    loadFirstMatchDate();

    api
      .get<MyPredictionBrief[]>("/predictions/mine/brief")
      .then((r) => {
        if (!cancelled) setMyPredByMatchId(predictionsByMatchId(r.data));
      })
      .catch(() => {
        if (!cancelled) setMyPredByMatchId({});
      });

    return () => {
      cancelled = true;
    };
  }, [timeZone]);

  const loadDay = useCallback(
    (dateKey: string) => {
      setLoading(true);
      api
        .get<Match[]>("/matches/by-day", {
          params: {
            date: dateKey,
            tz: timeZone,
            predicted_teams: "true",
          },
        })
        .then((r) => setMatches(r.data))
        .catch(() => setMatches([]))
        .finally(() => setLoading(false));
    },
    [timeZone],
  );

  useEffect(() => {
    loadDay(selectedDate);
  }, [selectedDate, loadDay]);

  const isToday = selectedDate === todayLocalDateKey();
  const tzLabel = formatTimeZoneLabel(timeZone, locale);
  const daysUntilStart =
    firstMatchLocalDate && compareLocalDateKeys(selectedDate, firstMatchLocalDate) < 0
      ? daysUntilLocalDate(selectedDate, firstMatchLocalDate)
      : null;
  const countdownLabel =
    daysUntilStart === 1
      ? t("dashboard.worldCupCountdown_one", { count: daysUntilStart })
      : daysUntilStart && daysUntilStart > 1
        ? t("dashboard.worldCupCountdown_other", { count: daysUntilStart })
        : null;

  const statusClass = (status: string) => {
    if (status === "completed") return "bg-green-100 text-green-700";
    if (status === "in_progress") return "bg-yellow-100 text-yellow-700";
    return "bg-blue-100 text-blue-700";
  };

  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <div>
          <h2 className="text-lg font-semibold text-pitch-900">
            {t("dashboard.matchCalendar")}
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {t("dashboard.timesInTimezone", { tz: tzLabel })}
          </p>
        </div>
        <Link
          to="/matches"
          className="text-sm text-pitch-600 hover:underline shrink-0 self-start sm:self-auto"
        >
          {t("dashboard.viewSchedule")}
        </Link>
      </div>

      <div className="flex items-center justify-between gap-2 mb-5">
        <button
          type="button"
          onClick={() => setSelectedDate((d) => shiftLocalDateKey(d, -1))}
          className="inline-flex items-center justify-center w-10 h-10 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-pitch-300 transition-colors"
          aria-label={t("dashboard.previousDay")}
        >
          <span aria-hidden className="text-lg leading-none">
            ←
          </span>
        </button>

        <div className="flex-1 text-center min-w-0 px-1">
          <p className="text-base sm:text-lg font-semibold text-gray-900 truncate">
            {formatCalendarDayHeader(selectedDate, locale)}
          </p>
          {!isToday && (
            <button
              type="button"
              onClick={() => setSelectedDate(todayLocalDateKey())}
              className="mt-1 text-xs font-medium text-pitch-600 hover:text-pitch-800 hover:underline"
            >
              {t("dashboard.today")}
            </button>
          )}
        </div>

        <button
          type="button"
          onClick={() => setSelectedDate((d) => shiftLocalDateKey(d, 1))}
          className="inline-flex items-center justify-center w-10 h-10 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-pitch-300 transition-colors"
          aria-label={t("dashboard.nextDay")}
        >
          <span aria-hidden className="text-lg leading-none">
            →
          </span>
        </button>
      </div>

      {countdownLabel && (
        <div className="rounded-xl border border-pitch-200 bg-gradient-to-br from-pitch-50 to-green-50 px-4 py-5 text-center mb-5">
          <span className="text-3xl" aria-hidden>
            ⚽
          </span>
          <p className="mt-2 text-base font-semibold text-pitch-900">{countdownLabel}</p>
          {firstMatchLocalDate && (
            <p className="mt-1 text-sm text-gray-600">
              {t("dashboard.worldCupStartsOn", {
                date: formatCalendarDayHeader(firstMatchLocalDate, locale),
              })}
            </p>
          )}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-10">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-pitch-600" />
        </div>
      ) : matches.length === 0 ? (
        daysUntilStart === null || daysUntilStart === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">
            {t("dashboard.noMatchesOnDay")}
          </p>
        ) : null
      ) : (
        <div className="space-y-3">
          {matches.map((m) => {
            const pred = myPredByMatchId[m.id];
            return (
              <Link
                key={m.id}
                to={`/matches/${m.match_number}`}
                className={`block rounded-xl border transition-all p-4 touch-manipulation hover:shadow-sm ${
                  pred
                    ? "border-gray-100 hover:border-pitch-300"
                    : "border-amber-300 bg-amber-50/40 hover:border-amber-400"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-gray-500">
                    <span className="font-semibold text-gray-700">#{m.match_number}</span>
                    <span className="text-gray-400">·</span>
                    <span>
                      {m.group_letter
                        ? t("matches.group", { letter: m.group_letter })
                        : t(`matches.${m.stage}`, formatStageSlug(m.stage))}
                    </span>
                  </div>
                  <span className="text-sm font-semibold text-pitch-800 tabular-nums">
                    {formatMatchTime(m.kickoff_utc, locale)}
                  </span>
                </div>

                <div className="flex items-center justify-center gap-3 sm:gap-6">
                  <div className="flex-1 flex items-center justify-end gap-2 min-w-0">
                    {m.home_team ? (
                      <>
                        <span className="font-semibold text-sm truncate text-right">
                          {localizedTeam(m.home_team, i18n.language)}
                        </span>
                        <img
                          src={m.home_team.flag_url}
                          alt=""
                          className="w-7 h-5 object-cover rounded-sm shrink-0"
                        />
                      </>
                    ) : (
                      <span className="text-sm text-gray-400">
                        {m.bracket_home_slot ?? t("dashboard.tbd")}
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-medium text-gray-400 shrink-0">
                    {t("dashboard.vs")}
                  </span>
                  <div className="flex-1 flex items-center gap-2 min-w-0">
                    {m.away_team ? (
                      <>
                        <img
                          src={m.away_team.flag_url}
                          alt=""
                          className="w-7 h-5 object-cover rounded-sm shrink-0"
                        />
                        <span className="font-semibold text-sm truncate">
                          {localizedTeam(m.away_team, i18n.language)}
                        </span>
                      </>
                    ) : (
                      <span className="text-sm text-gray-400">
                        {m.bracket_away_slot ?? t("dashboard.tbd")}
                      </span>
                    )}
                  </div>
                </div>

                <div
                  className={`mt-3 rounded-lg px-3 py-2 text-sm font-medium ${
                    pred
                      ? "bg-green-50 text-green-800 border border-green-100"
                      : "bg-amber-100 text-amber-900 border border-amber-200"
                  }`}
                >
                  {pred
                    ? t("dashboard.yourPredictionScore", {
                        home: pred.home,
                        away: pred.away,
                      })
                    : t("dashboard.noPredictionYet")}
                </div>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">
                  <span className="truncate">
                    {m.venue.name}, {m.venue.city}
                  </span>
                  <span
                    className={`inline-block px-2 py-0.5 rounded-full font-medium ${statusClass(m.status)}`}
                  >
                    {t(`matches.${m.status}`, m.status)}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
