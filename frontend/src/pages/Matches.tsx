import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { formatStageSlug } from "../utils/formatStage";
import VirtualGroupStandings from "../components/VirtualGroupStandings";
import { localizedTeam } from "../i18n/teamNames";
import type { Match, MyPrediction, VirtualGroupTable } from "../types";

function predictionsByMatchId(mine: MyPrediction[]) {
  const map: Record<number, { home: number; away: number }> = {};
  for (const p of mine) {
    map[p.match_id] = { home: p.home_score, away: p.away_score };
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

const LOCALE_MAP: Record<string, string> = {
  en: "en-US",
  nl: "nl-NL",
  pt: "pt-BR",
  de: "de-DE",
  he: "he-IL",
};

export default function Matches() {
  const { t, i18n } = useTranslation();
  const [matches, setMatches] = useState<Match[]>([]);
  const [myPredByMatchId, setMyPredByMatchId] = useState<
    Record<number, { home: number; away: number }>
  >({});
  const [virtualGroup, setVirtualGroup] = useState<VirtualGroupTable | null>(null);
  const [loading, setLoading] = useState(true);
  const [stage, setStage] = useState("");
  const [group, setGroup] = useState("");
  const [search, setSearch] = useState("");

  const locale = LOCALE_MAP[i18n.language] || "en-US";

  useEffect(() => {
    const params: Record<string, string> = { predicted_teams: "true" };
    if (stage) params.stage = stage;
    if (group) params.group = group;

    const loadMatches = api.get<Match[]>("/matches", { params });
    const loadMine = api
      .get<MyPrediction[]>("/predictions/mine")
      .catch(() => ({ data: [] as MyPrediction[] }));

    const showVirtualTable = !!group && (!stage || stage === "group");

    if (showVirtualTable) {
      setLoading(true);
      Promise.all([
        loadMatches,
        loadMine,
        api.get<VirtualGroupTable[]>("/predictions/virtual-groups", {
          params: { _t: Date.now() },
        }),
      ])
        .then(([mr, mineRes, vr]) => {
          setMatches(mr.data);
          setMyPredByMatchId(predictionsByMatchId(mineRes.data));
          const gl = group.trim().toUpperCase();
          const v =
            vr.data.find((x) => x.group_letter === gl) ??
            vr.data.find((x) => x.group_letter?.toUpperCase() === gl);
          setVirtualGroup(v ?? null);
        })
        .finally(() => setLoading(false));
    } else {
      setVirtualGroup(null);
      setLoading(true);
      Promise.all([loadMatches, loadMine])
        .then(([mr, mineRes]) => {
          setMatches(mr.data);
          setMyPredByMatchId(predictionsByMatchId(mineRes.data));
        })
        .finally(() => setLoading(false));
    }
  }, [stage, group]);

  const filtered = matches.filter((m) => {
    if (!search) return true;
    const q = search.toLowerCase();
    const homeName = localizedTeam(m.home_team, i18n.language).toLowerCase();
    const awayName = localizedTeam(m.away_team, i18n.language).toLowerCase();
    return (
      m.home_team?.name.toLowerCase().includes(q) ||
      m.away_team?.name.toLowerCase().includes(q) ||
      homeName.includes(q) ||
      awayName.includes(q) ||
      m.home_team?.fifa_code.toLowerCase().includes(q) ||
      m.away_team?.fifa_code.toLowerCase().includes(q) ||
      m.venue.name.toLowerCase().includes(q) ||
      m.venue.city.toLowerCase().includes(q)
    );
  });

  const grouped: Record<string, Match[]> = {};
  for (const m of filtered) {
    const dateKey = new Date(m.kickoff_utc).toLocaleDateString(locale, {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    (grouped[dateKey] ||= []).push(m);
  }

  const statusLabel = (s: string) => t(`matches.${s}`, s);

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <h1 className="text-2xl sm:text-3xl font-bold mb-6">{t("matches.title")}</h1>

      <div className="flex flex-wrap gap-2 sm:gap-3 mb-6">
        <select
          value={stage}
          onChange={(e) => {
            setStage(e.target.value);
            if (e.target.value !== "group") setGroup("");
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm focus:ring-2 focus:ring-pitch-600 outline-none"
        >
          {STAGE_KEYS.map((s) => (
            <option key={s.value} value={s.value}>
              {t(s.labelKey)}
            </option>
          ))}
        </select>

        {(stage === "" || stage === "group") && (
          <select
            value={group}
            onChange={(e) => setGroup(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm focus:ring-2 focus:ring-pitch-600 outline-none"
          >
            <option value="">{t("matches.allGroups")}</option>
            {GROUPS.filter(Boolean).map((g) => (
              <option key={g} value={g}>
                {t("matches.group", { letter: g })}
              </option>
            ))}
          </select>
        )}

        <input
          type="text"
          placeholder={t("matches.searchPlaceholder")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-pitch-600 outline-none"
        />
      </div>

      {(stage === "" || stage === "group") && !group && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          {t("matches.selectGroupForVirtual")}
        </div>
      )}

      {group && (!stage || stage === "group") && virtualGroup && (
        <div className="mb-8">
          <VirtualGroupStandings virtualGroup={virtualGroup} groupLetter={group} />
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
        </div>
      ) : filtered.length === 0 ? (
        <p className="text-gray-500 py-10 text-center">{t("matches.noMatches")}</p>
      ) : (
        Object.entries(grouped).map(([date, dayMatches]) => (
          <div key={date} className="mb-8">
            <h2 className="text-base sm:text-lg font-semibold text-gray-700 mb-3 sticky top-14 z-10 bg-gray-50/95 backdrop-blur-sm py-2 -mx-1 px-1 border-b border-gray-100 sm:border-0 sm:top-0">
              {date}
            </h2>
            <div className="space-y-3">
              {dayMatches.map((m) => {
                const myTip = myPredByMatchId[m.id];
                const userTipLocked = !(
                  m.status === "upcoming" && m.prediction_editable
                );
                return (
                <Link
                  key={m.id}
                  to={`/matches/${m.match_number}`}
                  className="block bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow p-3 sm:p-4 touch-manipulation"
                >
                  <div className="flex flex-col gap-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-gray-500 min-w-0">
                        <span className="font-semibold text-gray-700 whitespace-nowrap">
                          #{m.match_number}
                        </span>
                        <span className="text-gray-400 hidden sm:inline">·</span>
                        <span className="truncate max-w-[12rem] sm:max-w-none">
                          {m.group_letter
                            ? t("matches.group", { letter: m.group_letter })
                            : t(
                                `matches.${m.stage}`,
                                formatStageSlug(m.stage)
                              )}
                        </span>
                        <span className="text-gray-400">·</span>
                        <span className="tabular-nums whitespace-nowrap">
                          {new Date(m.kickoff_utc).toLocaleTimeString(locale, {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                      <span
                        className={`shrink-0 inline-flex px-2 py-1 rounded-full text-xs font-medium ${
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

                    <div className="grid grid-cols-[1fr_auto_1fr] gap-x-2 gap-y-1 items-center w-full min-w-0">
                      <div className="min-w-0 flex flex-col items-end text-right gap-0.5">
                        <div className="flex items-center gap-2 justify-end">
                          <span className="font-medium text-sm leading-snug line-clamp-2 break-words">
                            {m.home_team ? localizedTeam(m.home_team, i18n.language) : t("matches.tbd")}
                          </span>
                          {m.home_team && (
                            <img src={m.home_team.flag_url} alt="" className="w-7 h-5 object-cover rounded-sm shrink-0" />
                          )}
                        </div>
                        {m.bracket_home_slot && (
                          <span className="text-[11px] text-gray-500 font-mono">{m.bracket_home_slot}</span>
                        )}
                      </div>

                      <div className="shrink-0 px-1 text-center w-[4.5rem] sm:w-28">
                        {m.status === "completed" ? (
                          <div className="flex flex-col items-center gap-0.5">
                            <span className="font-bold text-base sm:text-lg leading-tight tabular-nums">
                              {m.home_score} - {m.away_score}
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

                      <div className="min-w-0 flex flex-col items-start text-left gap-0.5">
                        <div className="flex items-center gap-2">
                          {m.away_team && (
                            <img src={m.away_team.flag_url} alt="" className="w-7 h-5 object-cover rounded-sm shrink-0" />
                          )}
                          <span className="font-medium text-sm leading-snug line-clamp-2 break-words">
                            {m.away_team ? localizedTeam(m.away_team, i18n.language) : t("matches.tbd")}
                          </span>
                        </div>
                        {m.bracket_away_slot && (
                          <span className="text-[11px] text-gray-500 font-mono">{m.bracket_away_slot}</span>
                        )}
                      </div>
                    </div>

                    <div className="text-xs text-gray-400 truncate">
                      {m.venue.name} · {m.venue.city}
                    </div>
                  </div>
                </Link>
              );
              })}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
