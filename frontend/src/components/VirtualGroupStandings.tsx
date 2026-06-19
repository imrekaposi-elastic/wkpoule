import { useTranslation } from "react-i18next";
import { localizedTeamName } from "../i18n/teamNames";
import type { VirtualGroupTable } from "../types";

export function virtualRowClass(
  rankIndex: number,
  thirdQualifies: boolean | null | undefined
): string {
  if (rankIndex <= 1) return "bg-emerald-100/90 text-emerald-950";
  if (rankIndex === 2) {
    if (thirdQualifies === true) return "bg-amber-100/90 text-amber-950";
    if (thirdQualifies === false) return "bg-red-100/90 text-red-950";
    return "bg-gray-100 text-gray-800";
  }
  return "bg-red-100/90 text-red-950";
}

type Props = {
  virtualGroup: VirtualGroupTable;
  /** Group letter for title (e.g. match.group_letter or filter value) */
  groupLetter: string;
  /** Less visual noise: softer header, hint/legend tucked in details */
  compact?: boolean;
};

/** Virtual group table — same UI on Matches + Match detail */
export default function VirtualGroupStandings({
  virtualGroup,
  groupLetter,
  compact = false,
}: Props) {
  const { t, i18n } = useTranslation();

  const headerClass = compact
    ? "border-b border-gray-100 px-4 py-3"
    : "bg-pitch-800 text-white px-4 py-3";
  const titleClass = compact
    ? "font-semibold text-base text-pitch-800"
    : "font-bold text-lg";

  const legend = (
    <div className={compact ? "space-y-1 text-xs text-gray-600" : "space-y-1"}>
      <div>
        <span className="inline-block w-3 h-3 bg-emerald-200 rounded mr-1 align-middle" />{" "}
        {t("matches.virtualLegendGreen")}
      </div>
      <div>
        <span className="inline-block w-3 h-3 bg-amber-200 rounded mr-1 align-middle" />{" "}
        {t("matches.virtualLegendYellow")}
      </div>
      <div>
        <span className="inline-block w-3 h-3 bg-red-200 rounded mr-1 align-middle" />{" "}
        {t("matches.virtualLegendYellowRed")} · {t("matches.virtualLegendRed")}
      </div>
    </div>
  );

  return (
    <div
      className={`bg-white rounded-xl overflow-hidden border border-gray-100 ${
        compact ? "shadow-sm" : "shadow-md"
      }`}
    >
      <div className={headerClass}>
        <h2 className={titleClass}>
          {t("matches.virtualTitle")} · {t("matches.group", { letter: groupLetter })}
        </h2>
      </div>

      {compact ? (
        <details className="border-b border-gray-100 px-4 py-2 text-sm">
          <summary className="cursor-pointer text-gray-600 hover:text-pitch-700 select-none">
            {t("matches.virtualLearnMore")}
          </summary>
          <div className="mt-2 space-y-3 pb-1">
            <p className="text-sm text-gray-600">{t("matches.virtualHint")}</p>
            {legend}
          </div>
        </details>
      ) : (
        <>
          <p className="text-sm text-gray-600 px-4 pt-3">{t("matches.virtualHint")}</p>
        </>
      )}

      <div className="overflow-x-auto px-2 pb-2">
        <table className="w-full text-sm min-w-[32rem] mt-2">
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
            {virtualGroup.standings.map((s, i) => (
              <tr
                key={s.team_id}
                className={`border-b last:border-0 ${virtualRowClass(i, virtualGroup.third_place_qualifies)}`}
              >
                <td className="py-2.5 px-3 font-medium">
                  <span className="text-gray-600 mr-2 text-xs">{i + 1}</span>
                  {s.fifa_code}{" "}
                  <span className="text-gray-600 text-xs hidden sm:inline">
                    {localizedTeamName(s.fifa_code, s.team_name, i18n.language)}
                  </span>
                </td>
                <td className="py-2.5 px-1.5 text-center">{s.played}</td>
                <td className="py-2.5 px-1.5 text-center">{s.won}</td>
                <td className="py-2.5 px-1.5 text-center">{s.drawn}</td>
                <td className="py-2.5 px-1.5 text-center">{s.lost}</td>
                <td className="py-2.5 px-1.5 text-center">{s.goals_for}</td>
                <td className="py-2.5 px-1.5 text-center">{s.goals_against}</td>
                <td className="py-2.5 px-1.5 text-center">
                  {s.goal_difference > 0 ? `+${s.goal_difference}` : s.goal_difference}
                </td>
                <td className="py-2.5 px-2 text-center font-bold">{s.points}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!compact && (
        <div className="px-4 py-3 text-xs text-gray-600 border-t bg-gray-50">{legend}</div>
      )}
    </div>
  );
}
