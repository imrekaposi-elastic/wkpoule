import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import PlayerCard from "../components/PlayerCard";
import QualificationTables from "../components/QualificationTables";
import { localizedTeamName } from "../i18n/teamNames";
import {
  localizedTeamProfileField,
  teamProfileBulletLines,
} from "../utils/teamProfile";
import type { TeamDetail } from "../types";

export default function TeamDetailPage() {
  const { fifaCode } = useParams<{ fifaCode: string }>();
  const { t, i18n } = useTranslation();
  const [team, setTeam] = useState<TeamDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!fifaCode) return;
    setLoading(true);
    setNotFound(false);
    api
      .get<TeamDetail>(`/teams/${fifaCode}`)
      .then((r) => setTeam(r.data))
      .catch((err) => {
        if (err?.response?.status === 404) setNotFound(true);
        else setTeam(null);
      })
      .finally(() => setLoading(false));
  }, [fifaCode]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );
  }

  if (notFound || !team) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <p className="text-gray-600 mb-4">{t("teams.notFound")}</p>
        <Link to="/teams" className="text-pitch-700 font-medium hover:underline">
          {t("teams.backToList")}
        </Link>
      </div>
    );
  }

  const qualification = localizedTeamProfileField(team, "qualification", i18n.language);
  const strengths = teamProfileBulletLines(
    localizedTeamProfileField(team, "strengths", i18n.language),
  );
  const weaknesses = teamProfileBulletLines(
    localizedTeamProfileField(team, "weaknesses", i18n.language),
  );
  const displayName = localizedTeamName(team.fifa_code, team.name, i18n.language);

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <Link
        to="/teams"
        className="inline-flex items-center text-sm text-pitch-700 hover:text-pitch-900 mb-4"
      >
        ← {t("teams.backToList")}
      </Link>

      <header className="bg-white rounded-xl shadow-md overflow-hidden mb-8">
        <div className="bg-pitch-800 text-white px-4 sm:px-6 py-5 flex flex-wrap items-center gap-4">
          <img
            src={team.flag_url}
            alt=""
            className="w-16 h-11 object-cover rounded-md border-2 border-white/20 shadow"
          />
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold">{displayName}</h1>
            <p className="text-green-200 text-sm mt-1">
              {team.fifa_code} · {t("teams.group", { letter: team.group_letter })} ·{" "}
              {t("teams.ranking", { rank: team.world_ranking })}
            </p>
          </div>
        </div>

        <div className="p-4 sm:p-6 space-y-6">
          <section>
            <h2 className="text-lg font-bold text-pitch-900 mb-2">{t("teams.qualification")}</h2>
            <p className="text-gray-700 leading-relaxed mb-4">{qualification}</p>
            {team.qualification_data ? (
              <QualificationTables
                data={team.qualification_data}
                highlightCode={team.fifa_code}
              />
            ) : null}
          </section>

          <div className="grid md:grid-cols-2 gap-6">
            <section>
              <h2 className="text-lg font-bold text-emerald-800 mb-2">{t("teams.strengths")}</h2>
              <ul className="space-y-2">
                {strengths.map((line) => (
                  <li key={line} className="flex gap-2 text-sm text-gray-700">
                    <span className="text-emerald-600 shrink-0" aria-hidden>
                      ✓
                    </span>
                    {line}
                  </li>
                ))}
              </ul>
            </section>
            <section>
              <h2 className="text-lg font-bold text-rose-800 mb-2">{t("teams.weaknesses")}</h2>
              <ul className="space-y-2">
                {weaknesses.map((line) => (
                  <li key={line} className="flex gap-2 text-sm text-gray-700">
                    <span className="text-rose-500 shrink-0" aria-hidden>
                      !
                    </span>
                    {line}
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </div>
      </header>

      <section>
        <div className="flex flex-wrap items-end justify-between gap-3 mb-4">
          <h2 className="text-xl font-bold text-pitch-900">{t("teams.squad")}</h2>
          <p className="text-xs text-gray-500 max-w-md">{t("teams.squadNote")}</p>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 sm:gap-4">
          {team.players.map((player) => (
            <PlayerCard
              key={player.id}
              player={player}
              flagUrl={team.flag_url}
              positionLabel={t(`teams.player.position.${player.position}`, {
                defaultValue: player.position,
              })}
              heightLabel={t("teams.player.height")}
              weightLabel={t("teams.player.weight")}
              capsLabel={t("teams.player.caps")}
              clubLabel={t("teams.player.club")}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
