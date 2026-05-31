import { useTranslation } from "react-i18next";
import type { TeamPlayer } from "../types";

type Props = {
  players: TeamPlayer[];
};

export default function SquadTable({ players }: Props) {
  const { t } = useTranslation();

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
      <table className="min-w-full text-sm">
        <thead className="bg-pitch-50 text-left text-xs uppercase tracking-wide text-pitch-800">
          <tr>
            <th className="px-3 py-2.5 w-10">#</th>
            <th className="px-3 py-2.5">{t("teams.player.name")}</th>
            <th className="px-3 py-2.5">{t("teams.player.positionLabel")}</th>
            <th className="px-3 py-2.5">{t("teams.player.club")}</th>
            <th className="px-3 py-2.5 text-center">{t("teams.player.caps")}</th>
          </tr>
        </thead>
        <tbody>
          {players.map((player) => (
            <tr key={player.id} className="border-t border-gray-100 even:bg-gray-50/80">
              <td className="px-3 py-2.5 font-semibold text-pitch-800">{player.shirt_number}</td>
              <td className="px-3 py-2.5 font-medium text-gray-900 whitespace-nowrap">{player.name}</td>
              <td className="px-3 py-2.5 text-gray-700 whitespace-nowrap">
                {t(`teams.player.position.${player.position}`, { defaultValue: player.position })}
              </td>
              <td className="px-3 py-2.5 text-gray-700">{player.club}</td>
              <td className="px-3 py-2.5 text-center font-medium text-pitch-800">{player.caps}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
