import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import type { GroupTable } from "../types";

export default function Groups() {
  const { t } = useTranslation();
  const [groups, setGroups] = useState<GroupTable[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<GroupTable[]>("/groups")
      .then((r) => setGroups(r.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-pitch-900">{t("groups.title")}</h1>
        <p className="mt-3 max-w-3xl text-sm text-gray-600 leading-relaxed border-l-4 border-pitch-500 pl-4">
          {t("groups.subtitle")}
        </p>
      </header>

      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
        {groups.map((g) => (
          <div
            key={g.group_letter}
            className="bg-white rounded-xl shadow-md overflow-hidden"
          >
            <div className="bg-pitch-800 text-white px-4 py-3">
              <h2 className="font-bold text-lg">{t("groups.group", { letter: g.group_letter })}</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 border-b bg-gray-50">
                    <th className="text-left py-2 px-3 font-medium">{t("groups.team")}</th>
                    <th className="py-2 px-1.5 font-medium w-8">{t("groups.p")}</th>
                    <th className="py-2 px-1.5 font-medium w-8">{t("groups.w")}</th>
                    <th className="py-2 px-1.5 font-medium w-8">{t("groups.d")}</th>
                    <th className="py-2 px-1.5 font-medium w-8">{t("groups.l")}</th>
                    <th className="py-2 px-1.5 font-medium w-10">{t("groups.gf")}</th>
                    <th className="py-2 px-1.5 font-medium w-10">{t("groups.ga")}</th>
                    <th className="py-2 px-1.5 font-medium w-10">{t("groups.gd")}</th>
                    <th className="py-2 px-2 font-medium w-10">{t("groups.pts")}</th>
                  </tr>
                </thead>
                <tbody>
                  {g.standings.map((s, i) => (
                    <tr
                      key={s.team_id}
                      className={`border-b last:border-0 ${
                        i < 2
                          ? "bg-green-50"
                          : i === 2
                          ? "bg-yellow-50"
                          : ""
                      }`}
                    >
                      <td className="py-2.5 px-3 font-medium">
                        <span className="text-gray-400 mr-2 text-xs">
                          {i + 1}
                        </span>
                        {s.fifa_code}{" "}
                        <span className="text-gray-500 text-xs hidden sm:inline">
                          {s.team_name}
                        </span>
                      </td>
                      <td className="py-2.5 px-1.5 text-center">{s.played}</td>
                      <td className="py-2.5 px-1.5 text-center">{s.won}</td>
                      <td className="py-2.5 px-1.5 text-center">{s.drawn}</td>
                      <td className="py-2.5 px-1.5 text-center">{s.lost}</td>
                      <td className="py-2.5 px-1.5 text-center">{s.goals_for}</td>
                      <td className="py-2.5 px-1.5 text-center">{s.goals_against}</td>
                      <td className="py-2.5 px-1.5 text-center">
                        {s.goal_difference > 0
                          ? `+${s.goal_difference}`
                          : s.goal_difference}
                      </td>
                      <td className="py-2.5 px-2 text-center font-bold">{s.points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-4 py-2 text-xs text-gray-400 border-t">
              <span className="inline-block w-3 h-3 bg-green-100 rounded mr-1 align-middle" />{" "}
              {t("groups.qualifyAuto")}{" "}
              <span className="inline-block w-3 h-3 bg-yellow-100 rounded mr-1 ml-2 align-middle" />{" "}
              {t("groups.bestThird")}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
