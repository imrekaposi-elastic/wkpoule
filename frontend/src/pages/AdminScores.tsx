import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { localizedTeam } from "../i18n/teamNames";
import type { Match, PaginatedResponse } from "../types";

async function fetchAllMatches(params: Record<string, string>): Promise<Match[]> {
  const all: Match[] = [];
  let page = 1;
  let totalPages = 1;
  do {
    const { data } = await api.get<PaginatedResponse<Match>>("/matches", {
      params: { ...params, page, page_size: 20 },
    });
    all.push(...data.items);
    totalPages = data.total_pages;
    page += 1;
  } while (page <= totalPages);
  return all;
}

type Draft = { home: number; away: number; status: string };

const STAGE_FILTER: { value: string; labelKey: string }[] = [
  { value: "", labelKey: "matches.allStages" },
  { value: "group", labelKey: "matches.groupStage" },
  { value: "round_of_32", labelKey: "matches.roundOf32" },
  { value: "round_of_16", labelKey: "matches.roundOf16" },
  { value: "quarter_final", labelKey: "matches.quarterFinals" },
  { value: "semi_final", labelKey: "matches.semiFinals" },
  { value: "third_place", labelKey: "matches.thirdPlace" },
  { value: "final", labelKey: "matches.final" },
];

export default function AdminScores() {
  const { t, i18n } = useTranslation();
  const [matches, setMatches] = useState<Match[]>([]);
  const [drafts, setDrafts] = useState<Record<number, Draft>>({});
  const [loading, setLoading] = useState(true);
  const [stage, setStage] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [saving, setSaving] = useState<Record<number, boolean>>({});
  const [banner, setBanner] = useState<{ ok: boolean; text: string } | null>(null);

  const load = () => {
    setLoading(true);
    fetchAllMatches({})
      .then((items) => {
        setMatches(items);
        const d: Record<number, Draft> = {};
        for (const m of items) {
          d[m.id] = {
            home: m.home_score ?? 0,
            away: m.away_score ?? 0,
            status: m.status,
          };
        }
        setDrafts(d);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    return matches.filter((m) => {
      if (stage && m.stage !== stage) return false;
      if (statusFilter && m.status !== statusFilter) return false;
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      const homeName = localizedTeam(m.home_team, i18n.language).toLowerCase();
      const awayName = localizedTeam(m.away_team, i18n.language).toLowerCase();
      return (
        String(m.match_number).includes(q) ||
        m.home_team?.name.toLowerCase().includes(q) ||
        m.away_team?.name.toLowerCase().includes(q) ||
        homeName.includes(q) ||
        awayName.includes(q) ||
        m.home_team?.fifa_code.toLowerCase().includes(q) ||
        m.away_team?.fifa_code.toLowerCase().includes(q) ||
        m.venue.name.toLowerCase().includes(q)
      );
    });
  }, [matches, stage, statusFilter, search, i18n.language]);

  const sorted = useMemo(
    () => [...filtered].sort((a, b) => a.match_number - b.match_number),
    [filtered]
  );

  const updateDraft = (id: number, patch: Partial<Draft>) => {
    setDrafts((prev) => ({
      ...prev,
      [id]: { ...prev[id], ...patch },
    }));
  };

  const saveRow = async (m: Match) => {
    const d = drafts[m.id];
    if (!d) return;
    setSaving((s) => ({ ...s, [m.id]: true }));
    setBanner(null);
    try {
      const { data } = await api.patch<Match>(`/matches/${m.id}/score`, {
        home_score: d.home,
        away_score: d.away,
        status: d.status,
      });
      setMatches((prev) => prev.map((x) => (x.id === m.id ? data : x)));
      setDrafts((prev) => ({
        ...prev,
        [m.id]: {
          home: data.home_score ?? 0,
          away: data.away_score ?? 0,
          status: data.status,
        },
      }));
      setBanner({ ok: true, text: t("adminScores.savedRecalc") });
    } catch (e: unknown) {
      const d = (e as { response?: { data?: { detail?: unknown } } })?.response?.data
        ?.detail;
      let msg = t("adminScores.saveFailed");
      if (typeof d === "string") msg = d;
      else if (Array.isArray(d))
        msg =
          d
            .map((x: { msg?: string }) => x.msg)
            .filter(Boolean)
            .join("; ") || msg;
      setBanner({ ok: false, text: msg });
    } finally {
      setSaving((s) => ({ ...s, [m.id]: false }));
    }
  };

  const statusLabel = (s: string) => t(`matches.${s}`, s);

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <h1 className="text-2xl sm:text-3xl font-bold mb-2">{t("adminScores.title")}</h1>
      <p className="text-gray-600 mb-6 max-w-3xl">{t("adminScores.intro")}</p>

      {banner && (
        <div
          className={`mb-4 rounded-lg px-4 py-3 text-sm ${
            banner.ok
              ? "bg-green-50 text-green-900 border border-green-200"
              : "bg-red-50 text-red-900 border border-red-200"
          }`}
        >
          {banner.text}
        </div>
      )}

      <div className="flex flex-wrap gap-3 mb-6">
        <select
          value={stage}
          onChange={(e) => setStage(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm focus:ring-2 focus:ring-pitch-600 outline-none"
        >
          {STAGE_FILTER.map((s) => (
            <option key={s.value || "all"} value={s.value}>
              {t(s.labelKey)}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm focus:ring-2 focus:ring-pitch-600 outline-none"
        >
          <option value="">{t("adminScores.allStatuses")}</option>
          <option value="upcoming">{statusLabel("upcoming")}</option>
          <option value="in_progress">{statusLabel("in_progress")}</option>
          <option value="completed">{statusLabel("completed")}</option>
        </select>
        <input
          type="text"
          placeholder={t("adminScores.searchPlaceholder")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-pitch-600 outline-none"
        />
        <button
          type="button"
          onClick={load}
          className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
        >
          {t("adminScores.refresh")}
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
        </div>
      ) : sorted.length === 0 ? (
        <p className="text-gray-500 py-10 text-center">{t("matches.noMatches")}</p>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-x-auto overscroll-x-contain">
          <table className="w-full text-sm min-w-[44rem]">
            <thead>
              <tr className="text-left text-gray-500 border-b bg-gray-50">
                <th className="py-3 px-3 font-medium w-16">#</th>
                <th className="py-3 px-3 font-medium min-w-[200px]">{t("adminScores.match")}</th>
                <th className="py-3 px-3 font-medium">{t("adminScores.score")}</th>
                <th className="py-3 px-3 font-medium">{t("adminScores.status")}</th>
                <th className="py-3 px-3 font-medium w-28">{t("adminScores.action")}</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((m) => {
                const d = drafts[m.id];
                if (!d) return null;
                return (
                  <tr key={m.id} className="border-b last:border-0 hover:bg-gray-50/80">
                    <td className="py-2.5 px-3 align-middle text-gray-500">{m.match_number}</td>
                    <td className="py-2.5 px-3 align-middle">
                      <div className="font-medium text-gray-900">
                        {m.home_team?.fifa_code || "—"} vs {m.away_team?.fifa_code || "—"}
                      </div>
                      <div className="text-xs text-gray-500">
                        {m.group_letter
                          ? t("matches.group", { letter: m.group_letter })
                          : t(`matches.${m.stage}`, m.stage)}
                        {" · "}
                        {m.venue.city}
                      </div>
                    </td>
                    <td className="py-2.5 px-3 align-middle">
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min={0}
                          max={30}
                          value={d.home}
                          onChange={(e) =>
                            updateDraft(m.id, { home: Number(e.target.value) || 0 })
                          }
                          className="w-14 text-center border border-gray-300 rounded px-1 py-1"
                        />
                        <span className="text-gray-400">-</span>
                        <input
                          type="number"
                          min={0}
                          max={30}
                          value={d.away}
                          onChange={(e) =>
                            updateDraft(m.id, { away: Number(e.target.value) || 0 })
                          }
                          className="w-14 text-center border border-gray-300 rounded px-1 py-1"
                        />
                      </div>
                    </td>
                    <td className="py-2.5 px-3 align-middle">
                      <select
                        value={d.status}
                        onChange={(e) => updateDraft(m.id, { status: e.target.value })}
                        className="border border-gray-300 rounded px-2 py-1 text-xs"
                      >
                        <option value="upcoming">{statusLabel("upcoming")}</option>
                        <option value="in_progress">{statusLabel("in_progress")}</option>
                        <option value="completed">{statusLabel("completed")}</option>
                      </select>
                    </td>
                    <td className="py-2.5 px-3 align-middle">
                      <button
                        type="button"
                        disabled={!!saving[m.id]}
                        onClick={() => saveRow(m)}
                        className="px-3 py-1.5 bg-pitch-600 text-white rounded-lg text-xs font-medium hover:bg-pitch-700 disabled:opacity-50"
                      >
                        {saving[m.id] ? t("adminScores.saving") : t("adminScores.apply")}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="mt-6 text-xs text-gray-500 max-w-3xl">{t("adminScores.footerHint")}</p>
    </div>
  );
}
