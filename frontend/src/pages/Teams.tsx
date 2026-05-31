import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { localizedTeamName } from "../i18n/teamNames";
import { localizedTeamProfileField } from "../utils/teamProfile";
import type { TeamSummary } from "../types";

export default function Teams() {
  const { t, i18n } = useTranslation();
  const [teams, setTeams] = useState<TeamSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    api
      .get<TeamSummary[]>("/teams")
      .then((r) => setTeams(r.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const grouped = useMemo(() => {
    const map = new Map<string, TeamSummary[]>();
    for (const team of teams) {
      const list = map.get(team.group_letter) ?? [];
      list.push(team);
      map.set(team.group_letter, list);
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [teams]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 text-center text-red-600">
        {t("teams.loadError")}
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <header className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-pitch-900">{t("teams.title")}</h1>
        <p className="mt-3 max-w-3xl text-sm text-gray-600 leading-relaxed border-l-4 border-pitch-500 pl-4">
          {t("teams.subtitle")}
        </p>
      </header>

      <div className="space-y-8">
        {grouped.map(([letter, groupTeams]) => (
          <section key={letter}>
            <h2 className="text-lg font-bold text-pitch-800 mb-4">
              {t("teams.group", { letter })}
            </h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {groupTeams.map((team) => (
                <Link
                  key={team.fifa_code}
                  to={`/teams/${team.fifa_code}`}
                  className="bg-white rounded-xl shadow-md hover:shadow-lg border border-gray-100 overflow-hidden transition-shadow flex flex-col"
                >
                  <div className="bg-pitch-800 text-white px-4 py-3 flex items-center gap-3">
                    <img
                      src={team.flag_url}
                      alt=""
                      className="w-10 h-7 object-cover rounded-sm border border-white/20"
                      loading="lazy"
                    />
                    <div className="min-w-0">
                      <p className="font-bold truncate">
                        {localizedTeamName(team.fifa_code, team.name, i18n.language)}
                      </p>
                      <p className="text-xs text-green-200">
                        {team.fifa_code} · {t("teams.ranking", { rank: team.world_ranking })}
                      </p>
                    </div>
                  </div>
                  <p className="p-4 text-sm text-gray-600 line-clamp-4 flex-1">
                    {localizedTeamProfileField(team, "qualification", i18n.language)}
                  </p>
                  <div className="px-4 pb-4">
                    <span className="text-sm font-medium text-pitch-700 hover:text-pitch-900">
                      {t("teams.viewTeam")} →
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
