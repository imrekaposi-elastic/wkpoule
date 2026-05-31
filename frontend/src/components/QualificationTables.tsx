import { useTranslation } from "react-i18next";
import { localizedTeamName } from "../i18n/teamNames";
import type { QualificationData } from "../types";

type Props = {
  data: QualificationData;
  highlightCode: string;
};

function competitionLabel(data: QualificationData, language: string): string {
  const lang = language.split("-")[0];
  return data.competition[lang] ?? data.competition.en ?? "";
}

export default function QualificationTables({ data, highlightCode }: Props) {
  const { t, i18n } = useTranslation();
  const competition = competitionLabel(data, i18n.language);

  return (
    <div className="space-y-6">
      {competition ? (
        <p className="text-sm font-medium text-pitch-800">{competition}</p>
      ) : null}

      {data.standings.length > 0 ? (
        <section>
          <h3 className="text-base font-bold text-pitch-900 mb-2">
            {t("teams.qualificationStandings")}
          </h3>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="min-w-full text-sm">
              <thead className="bg-pitch-50 text-left text-xs uppercase tracking-wide text-pitch-800">
                <tr>
                  <th className="px-3 py-2">#</th>
                  <th className="px-3 py-2">{t("teams.qualificationTable.team")}</th>
                  <th className="px-3 py-2 text-center">{t("teams.qualificationTable.played")}</th>
                  <th className="px-3 py-2 text-center">{t("teams.qualificationTable.won")}</th>
                  <th className="px-3 py-2 text-center">{t("teams.qualificationTable.drawn")}</th>
                  <th className="px-3 py-2 text-center">{t("teams.qualificationTable.lost")}</th>
                  <th className="px-3 py-2 text-center">{t("teams.qualificationTable.goalsFor")}</th>
                  <th className="px-3 py-2 text-center">{t("teams.qualificationTable.goalsAgainst")}</th>
                  <th className="px-3 py-2 text-center">{t("teams.qualificationTable.goalDiff")}</th>
                  <th className="px-3 py-2 text-center">{t("teams.qualificationTable.points")}</th>
                </tr>
              </thead>
              <tbody>
                {data.standings.map((row) => {
                  const isHighlight =
                    row.highlight || row.code?.toUpperCase() === highlightCode.toUpperCase();
                  return (
                    <tr
                      key={`${row.pos}-${row.code ?? row.name}`}
                      className={isHighlight ? "bg-amber-50 font-semibold" : "bg-white even:bg-gray-50"}
                    >
                      <td className="px-3 py-2">{row.pos}</td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        {row.code
                          ? localizedTeamName(row.code, row.name, i18n.language)
                          : row.name}
                      </td>
                      <td className="px-3 py-2 text-center">{row.p}</td>
                      <td className="px-3 py-2 text-center">{row.w}</td>
                      <td className="px-3 py-2 text-center">{row.d}</td>
                      <td className="px-3 py-2 text-center">{row.l}</td>
                      <td className="px-3 py-2 text-center">{row.gf}</td>
                      <td className="px-3 py-2 text-center">{row.ga}</td>
                      <td className="px-3 py-2 text-center">{row.gd > 0 ? `+${row.gd}` : row.gd}</td>
                      <td className="px-3 py-2 text-center">{row.pts}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {data.results.length > 0 ? (
        <section>
          <h3 className="text-base font-bold text-pitch-900 mb-2">
            {t("teams.qualificationResults")}
          </h3>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="min-w-full text-sm">
              <thead className="bg-pitch-50 text-left text-xs uppercase tracking-wide text-pitch-800">
                <tr>
                  <th className="px-3 py-2">{t("teams.qualificationTable.date")}</th>
                  <th className="px-3 py-2">{t("teams.qualificationTable.home")}</th>
                  <th className="px-3 py-2 text-center">{t("teams.qualificationTable.score")}</th>
                  <th className="px-3 py-2">{t("teams.qualificationTable.away")}</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((match) => (
                  <tr key={`${match.date}-${match.home}-${match.away}`} className="bg-white even:bg-gray-50">
                    <td className="px-3 py-2 whitespace-nowrap">{match.date}</td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      {localizedTeamName(match.home, match.home, i18n.language)}
                    </td>
                    <td className="px-3 py-2 text-center font-semibold">{match.score}</td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      {localizedTeamName(match.away, match.away, i18n.language)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
