import type { TeamPlayer } from "../types";

function playerInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

const POSITION_COLORS: Record<string, string> = {
  GK: "bg-amber-500",
  DF: "bg-sky-600",
  MF: "bg-emerald-600",
  FW: "bg-rose-600",
};

type Props = {
  player: TeamPlayer;
  flagUrl: string;
  positionLabel: string;
  heightLabel: string;
  weightLabel: string;
  capsLabel: string;
  clubLabel: string;
};

export default function PlayerCard({
  player,
  flagUrl,
  positionLabel,
  heightLabel,
  weightLabel,
  capsLabel,
  clubLabel,
}: Props) {
  const posColor = POSITION_COLORS[player.position] ?? "bg-gray-600";

  return (
    <article className="group relative bg-gradient-to-br from-white via-amber-50/80 to-amber-100/60 rounded-xl border-2 border-amber-200/90 shadow-md hover:shadow-lg transition-shadow overflow-hidden">
      <div
        className="absolute inset-0 opacity-[0.07] pointer-events-none"
        style={{
          backgroundImage:
            "repeating-linear-gradient(45deg, #92400e 0, #92400e 1px, transparent 0, transparent 50%)",
          backgroundSize: "8px 8px",
        }}
        aria-hidden
      />
      <div className="relative p-3 sm:p-4 flex flex-col h-full">
        <div className="flex items-start justify-between gap-2 mb-3">
          <span
            className={`inline-flex items-center justify-center min-w-[2rem] h-8 px-2 rounded-md text-white text-sm font-black shadow ${posColor}`}
          >
            {player.shirt_number}
          </span>
          <img
            src={flagUrl}
            alt=""
            className="w-8 h-6 object-cover rounded-sm border border-gray-200 shadow-sm"
            loading="lazy"
          />
        </div>

        <div className="relative mx-auto mb-3 w-full max-w-[140px] aspect-[3/4] rounded-lg border-2 border-white shadow-inner bg-gradient-to-b from-slate-100 to-slate-200 overflow-hidden">
          <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-pitch-700/10 to-pitch-900/20">
            <span className="text-3xl sm:text-4xl font-black text-pitch-800/70 tracking-tight">
              {playerInitials(player.name)}
            </span>
          </div>
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent px-2 py-1.5">
            <p className="text-[10px] font-bold uppercase tracking-wider text-amber-300">
              {positionLabel}
            </p>
          </div>
        </div>

        <h3 className="text-center font-bold text-pitch-900 text-sm sm:text-base leading-tight mb-3 min-h-[2.5rem] flex items-center justify-center">
          {player.name}
        </h3>

        <dl className="mt-auto space-y-1.5 text-xs text-gray-700 border-t border-amber-200/80 pt-3">
          <div className="flex justify-between gap-2">
            <dt className="text-gray-500 shrink-0">{clubLabel}</dt>
            <dd className="font-medium text-right truncate">{player.club}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-gray-500">{heightLabel}</dt>
            <dd className="font-medium">
              {player.height_cm > 0 ? `${player.height_cm} cm` : "—"}
            </dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-gray-500">{weightLabel}</dt>
            <dd className="font-medium">
              {player.weight_kg > 0 ? `${player.weight_kg} kg` : "—"}
            </dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-gray-500">{capsLabel}</dt>
            <dd className="font-bold text-pitch-800">{player.caps}</dd>
          </div>
        </dl>
      </div>
    </article>
  );
}
