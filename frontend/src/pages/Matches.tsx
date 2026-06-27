import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import Pagination from "../components/Pagination";
import { formatStageSlug } from "../utils/formatStage";
import { canEditMatchPrediction } from "../utils/predictionLock";
import VirtualGroupStandings from "../components/VirtualGroupStandings";
import { resolveLocale } from "../i18n/languages";
import { localizedTeam } from "../i18n/teamNames";
import {
  readMatchesStageFilter,
  writeMatchesStageFilter,
} from "../utils/matchesStageFilterStorage";
import type { Match, MyPredictionBrief, PaginatedResponse, VirtualGroupTable } from "../types";

function predictionsByMatchId(mine: MyPredictionBrief[]) {
  const map: Record<number, { home: number; away: number; points: number | null }> = {};
  for (const p of mine) {
    map[p.match_id] = {
      home: p.home_score,
      away: p.away_score,
      points: p.points ?? null,
    };
  }
  return map;
}

const STAGE_KEYS: { value: string; labelKey: string }[] = [
  { value: "", labelKey: "matches.allStages" },
  { value: "group", labelKey: "matches.groupStage" },
  { value: "round_of_32", labelKey: "matches.roundOf32" },
  { value: "round_of_16", labelKey: "matches.roundOf16" },
  { value: "quarter_final", labelKey: "matches.quarterFinals" },
  { value: "semi_final", labelKey: "matches.semiFinals" },
  { value: "third_place", labelKey: "matches.thirdPlace" },
  { value: "final", labelKey: "matches.final" },
];

const GROUPS = ["", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"];

function shouldShowVirtualTable(stageVal: string, groupVal: string) {
  return !!groupVal && (!stageVal || stageVal === "group");
}

export default function Matches() {
  const { t, i18n } = useTranslation();
  const initialFilter = readMatchesStageFilter();
  const [matches, setMatches] = useState<Match[]>([]);
  const [myPredByMatchId, setMyPredByMatchId] = useState<
    Record<number, { home: number; away: number; points: number | null }>
  >({});
  const [virtualGroup, setVirtualGroup] = useState<VirtualGroupTable | null>(null);
  const [loading, setLoading] = useState(true);
  const [virtualLoading, setVirtualLoading] = useState(false);
  const [stage, setStage] = useState(initialFilter.stage);
  const [group, setGroup] = useState(initialFilter.group);
  const [stagePinned, setStagePinned] = useState(initialFilter.pinned);
  const [search, setSearch] = useState("");
  const [searchApplied, setSearchApplied] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const loadGenerationRef = useRef(0);
  const scrollToMatchIdRef = useRef<number | null>(null);

  const locale = resolveLocale(i18n.language);

  const persistStageFilter = useCallback(
    (stageVal: string, groupVal: string, pinned: boolean) => {
      writeMatchesStageFilter(stageVal, groupVal, pinned);
    },
    [],
  );

  const handleStageChange = useCallback(
    (stageVal: string) => {
      const nextGroup = stageVal !== "group" && stageVal !== "" ? "" : group;
      setStage(stageVal);
      if (stageVal !== "group" && stageVal !== "") {
        setGroup("");
      }
      if (stagePinned) {
        persistStageFilter(stageVal, nextGroup, true);
      }
    },
    [group, persistStageFilter, stagePinned],
  );

  const handleGroupChange = useCallback(
    (groupVal: string) => {
      setGroup(groupVal);
      if (stagePinned) {
        persistStageFilter(stage, groupVal, true);
      }
    },
    [persistStageFilter, stage, stagePinned],
  );

  const toggleStagePin = useCallback(() => {
    const nextPinned = !stagePinned;
    setStagePinned(nextPinned);
    persistStageFilter(stage, group, nextPinned);
  }, [group, persistStageFilter, stage, stagePinned]);

  useEffect(() => {
    api
      .get<MyPredictionBrief[]>("/predictions/mine/brief")
      .then((r) => setMyPredByMatchId(predictionsByMatchId(r.data)))
      .catch(() => setMyPredByMatchId({}));
  }, []);

  const fetchMatchesPage = useCallback(
    async (p: number, stageVal: string, groupVal: string, searchVal: string) => {
      const params: Record<string, string | number> = {
        predicted_teams: "true",
        page: p,
        page_size: 20,
      };
      if (stageVal) params.stage = stageVal;
      if (groupVal) params.group = groupVal;
      if (searchVal.trim()) params.search = searchVal.trim();

      const mr = await api.get<PaginatedResponse<Match>>("/matches", { params });
      return mr.data;
    },
    [],
  );

  const runLoad = useCallback(
    async (opts: {
      page: number;
      stageVal: string;
      groupVal: string;
      searchVal: string;
      autoFocus: boolean;
    }) => {
      const gen = ++loadGenerationRef.current;
      setLoading(true);
      scrollToMatchIdRef.current = null;

      try {
        let currentPage = opts.page;
        let data = await fetchMatchesPage(
          currentPage,
          opts.stageVal,
          opts.groupVal,
          opts.searchVal,
        );

        if (opts.autoFocus) {
          while (
            data.items.length > 0 &&
            data.items.every((m) => m.status === "completed") &&
            currentPage < data.total_pages
          ) {
            currentPage++;
            data = await fetchMatchesPage(
              currentPage,
              opts.stageVal,
              opts.groupVal,
              opts.searchVal,
            );
          }
          const firstOpenIdx = data.items.findIndex((m) => m.status !== "completed");
          if (firstOpenIdx > 0) {
            scrollToMatchIdRef.current = data.items[firstOpenIdx].id;
          }
        }

        if (gen !== loadGenerationRef.current) return;

        setMatches(data.items);
        setPage(data.page);
        setTotalPages(data.total_pages);
        setTotal(data.total);
      } catch {
        if (gen !== loadGenerationRef.current) return;
        setMatches([]);
        setTotal(0);
        setTotalPages(1);
      } finally {
        if (gen === loadGenerationRef.current) setLoading(false);
      }
    },
    [fetchMatchesPage],
  );

  const handlePageChange = useCallback(
    (p: number) => {
      runLoad({
        page: p,
        stageVal: stage,
        groupVal: group,
        searchVal: searchApplied,
        autoFocus: false,
      });
    },
    [stage, group, searchApplied, runLoad],
  );

  useEffect(() => {
    runLoad({
      page: 1,
      stageVal: stage,
      groupVal: group,
      searchVal: searchApplied,
      autoFocus: true,
    });
  }, [stage, group, searchApplied, runLoad]);

  useLayoutEffect(() => {
    if (loading || scrollToMatchIdRef.current === null) return;
    const matchId = scrollToMatchIdRef.current;
    scrollToMatchIdRef.current = null;
    document
      .getElementById(`match-row-${matchId}`)
      ?.scrollIntoView({ behavior: "auto", block: "start" });
  }, [loading, matches]);

  const loadVirtualGroup = useCallback((stageVal: string, groupVal: string) => {
    if (!shouldShowVirtualTable(stageVal, groupVal)) {
      setVirtualGroup(null);
      setVirtualLoading(false);
      return;
    }

    setVirtualLoading(true);
    api
      .get<VirtualGroupTable[]>("/predictions/virtual-groups")
      .then((vr) => {
        const gl = groupVal.trim().toUpperCase();
        const v =
          vr.data.find((x) => x.group_letter === gl) ??
          vr.data.find((x) => x.group_letter?.toUpperCase() === gl);
        setVirtualGroup(v ?? null);
      })
      .catch(() => setVirtualGroup(null))
      .finally(() => setVirtualLoading(false));
  }, []);

  useEffect(() => {
    loadVirtualGroup(stage, group);
  }, [stage, group, loadVirtualGroup]);

  const grouped: Record<string, Match[]> = {};
  for (const m of matches) {
    const dateKey = new Date(m.kickoff_utc).toLocaleDateString(locale, {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    (grouped[dateKey] ||= []).push(m);
  }

  const statusLabel = (s: string) => t(`matches.${s}`, s);
  const showVirtualTable = shouldShowVirtualTable(stage, group);
  const showGroupFilter = stage === "" || stage === "group";

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <h1 className="text-2xl sm:text-3xl font-bold mb-6">{t("matches.title")}</h1>

      <div className="mb-6 bg-white rounded-xl border border-gray-100 shadow-sm p-4 space-y-3">
        <div className="flex flex-wrap gap-2 sm:gap-3 items-center">
          <select
            value={stage}
            onChange={(e) => handleStageChange(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg bg-white text-sm focus:ring-2 focus:ring-pitch-600 outline-none"
          >
            {STAGE_KEYS.map((s) => (
              <option key={s.value} value={s.value}>
                {t(s.labelKey)}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={toggleStagePin}
            aria-pressed={stagePinned}
            aria-label={stagePinned ? t("matches.unpinStage") : t("matches.pinStage")}
            title={stagePinned ? t("matches.unpinStage") : t("matches.pinStage")}
            className={`inline-flex items-center justify-center px-3 py-2 rounded-lg border text-sm transition-colors ${
              stagePinned
                ? "border-pitch-600 bg-pitch-50 text-pitch-800"
                : "border-gray-200 bg-white text-gray-500 hover:bg-gray-50"
            }`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              className="w-4 h-4"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M9.69 18.933l.003.001C9.89 19.02 10 19 10 19s.11.02.308-.066l.002-.001.006-.003.018-.008a5.741 5.741 0 00.281-.14c.186-.096.446-.24.757-.433.62-.384 1.445-.966 2.274-1.765C15.302 14.988 17 12.493 17 9A7 7 0 103 9c0 3.492 1.698 5.988 3.355 7.584a13.731 13.731 0 002.273 1.765 11.842 11.842 0 00.976.544l.062.029.018.008.006.003zM10 11.25a2.25 2.25 0 100-4.5 2.25 2.25 0 000 4.5z"
                clipRule="evenodd"
              />
            </svg>
          </button>

          {showGroupFilter && (
            <select
              value={group}
              onChange={(e) => handleGroupChange(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg bg-white text-sm focus:ring-2 focus:ring-pitch-600 outline-none"
            >
              <option value="">{t("matches.allGroups")}</option>
              {GROUPS.filter(Boolean).map((g) => (
                <option key={g} value={g}>
                  {t("matches.group", { letter: g })}
                </option>
              ))}
            </select>
          )}
        </div>

        {showGroupFilter && !group && (
          <p className="text-xs text-gray-500">{t("matches.selectGroupForVirtual")}</p>
        )}

        <div className="flex flex-wrap gap-2">
          <input
            type="text"
            placeholder={t("matches.searchPlaceholder")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") setSearchApplied(search);
            }}
            className="flex-1 min-w-[160px] px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-pitch-600 outline-none"
          />
          <button
            type="button"
            onClick={() => setSearchApplied(search)}
            className="px-4 py-2 rounded-lg bg-pitch-700 text-white text-sm font-medium hover:bg-pitch-800"
          >
            {t("matches.searchApply")}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
        </div>
      ) : matches.length === 0 ? (
        <p className="text-gray-500 py-10 text-center">{t("matches.noMatches")}</p>
      ) : (
        <>
          {Object.entries(grouped).map(([date, dayMatches]) => (
            <div key={date} className="mb-6">
              <h2 className="text-sm font-medium text-gray-500 mb-2 pb-1 border-b border-gray-100">
                {date}
              </h2>
              <div className="space-y-2">
                {dayMatches.map((m) => {
                  const myTip = myPredByMatchId[m.id];
                  const userTipLocked = !canEditMatchPrediction(
                    m.status,
                    m.kickoff_utc,
                    m.prediction_editable,
                  );
                  const isCompleted = m.status === "completed";

                  return (
                    <Link
                      key={m.id}
                      id={`match-row-${m.id}`}
                      to={`/matches/${m.match_number}`}
                      className="block bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow p-3 sm:p-4 touch-manipulation scroll-mt-20"
                    >
                      <div className="flex flex-col gap-2.5">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-gray-500 min-w-0">
                            <span className="font-semibold text-gray-700 whitespace-nowrap">
                              #{m.match_number}
                            </span>
                            <span aria-hidden="true">·</span>
                            <span className="truncate max-w-[10rem] sm:max-w-none">
                              {m.group_letter
                                ? t("matches.group", { letter: m.group_letter })
                                : t(`matches.${m.stage}`, formatStageSlug(m.stage))}
                            </span>
                            <span aria-hidden="true">·</span>
                            <span className="tabular-nums whitespace-nowrap">
                              {new Date(m.kickoff_utc).toLocaleTimeString(locale, {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>
                          <div className="flex flex-wrap items-center gap-2 shrink-0">
                            {isCompleted &&
                              (myTip ? (
                                myTip.points !== null ? (
                                  <span
                                    className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold tabular-nums ${
                                      myTip.points > 0
                                        ? "bg-emerald-100 text-emerald-800"
                                        : "bg-gray-100 text-gray-600"
                                    }`}
                                  >
                                    {t("matches.pointsEarned", { count: myTip.points })}
                                  </span>
                                ) : null
                              ) : (
                                <span className="inline-flex px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                                  {t("matches.noTip")}
                                </span>
                              ))}
                            <span
                              className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                                m.status === "completed"
                                  ? "bg-green-100 text-green-700"
                                  : m.status === "in_progress"
                                    ? "bg-yellow-100 text-yellow-700"
                                    : "bg-blue-100 text-blue-700"
                              }`}
                            >
                              {statusLabel(m.status)}
                            </span>
                          </div>
                        </div>

                        <div className="grid grid-cols-[1fr_auto_1fr] gap-x-2 items-center w-full min-w-0">
                          <div className="min-w-0 flex items-center gap-2 justify-end">
                            <span className="font-medium text-sm leading-snug line-clamp-2 break-words text-right">
                              {m.home_team
                                ? localizedTeam(m.home_team, i18n.language)
                                : t("matches.tbd")}
                            </span>
                            {m.home_team && (
                              <img
                                src={m.home_team.flag_url}
                                alt=""
                                className="w-7 h-5 object-cover rounded-sm shrink-0"
                              />
                            )}
                          </div>

                          <div className="shrink-0 px-1 text-center w-[4.5rem] sm:w-28">
                            {isCompleted ? (
                              <div className="flex flex-col items-center gap-0.5">
                                <span className="font-bold text-base sm:text-lg leading-tight tabular-nums">
                                  {m.home_score} – {m.away_score}
                                </span>
                                {myTip && (
                                  <span
                                    className={`text-[10px] sm:text-xs font-medium leading-tight ${
                                      userTipLocked ? "text-gray-400" : "text-pitch-700"
                                    }`}
                                  >
                                    {t("matches.yourTip")}: {myTip.home}–{myTip.away}
                                  </span>
                                )}
                              </div>
                            ) : myTip ? (
                              <div className="flex flex-col items-center gap-0.5">
                                <span
                                  className={`font-semibold text-base sm:text-lg leading-tight tabular-nums ${
                                    userTipLocked ? "text-gray-400" : "text-pitch-700"
                                  }`}
                                >
                                  {myTip.home} – {myTip.away}
                                </span>
                                <span
                                  className={`text-[10px] leading-tight ${
                                    userTipLocked ? "text-gray-400" : "text-gray-500"
                                  }`}
                                >
                                  {t("matches.yourTip")}
                                </span>
                              </div>
                            ) : (
                              <span className="text-gray-400 text-sm">{t("matches.vs")}</span>
                            )}
                          </div>

                          <div className="min-w-0 flex items-center gap-2">
                            {m.away_team && (
                              <img
                                src={m.away_team.flag_url}
                                alt=""
                                className="w-7 h-5 object-cover rounded-sm shrink-0"
                              />
                            )}
                            <span className="font-medium text-sm leading-snug line-clamp-2 break-words">
                              {m.away_team
                                ? localizedTeam(m.away_team, i18n.language)
                                : t("matches.tbd")}
                            </span>
                          </div>
                        </div>

                        <div className="text-xs text-gray-400 truncate hidden sm:block">
                          {m.venue.name} · {m.venue.city}
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
          <Pagination
            page={page}
            totalPages={totalPages}
            total={total}
            onPageChange={handlePageChange}
            disabled={loading}
          />
        </>
      )}

      {showVirtualTable && (
        <section className="mt-10 pt-8 border-t border-gray-100">
          {virtualLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pitch-600" />
            </div>
          ) : (
            virtualGroup && (
              <VirtualGroupStandings
                virtualGroup={virtualGroup}
                groupLetter={group}
                compact
              />
            )
          )}
        </section>
      )}
    </div>
  );
}
