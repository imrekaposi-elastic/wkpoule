import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { formatStageSlugSpacesOnly } from "../utils/formatStage";
import { localizedTeamName, localizedVenueCountry } from "../i18n/teamNames";
import type { VenueDetail, VenueScheduledMatch } from "../types";

function Stars({ count, max = 5 }: { count: number; max?: number }) {
  return (
    <span className="inline-flex gap-0.5" aria-hidden>
      {Array.from({ length: max }, (_, i) => (
        <svg
          key={i}
          className={`w-4 h-4 ${i < count ? "text-yellow-400" : "text-gray-300"}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.286 3.957a1 1 0 00.95.69h4.162c.969 0 1.371 1.24.588 1.81l-3.37 2.448a1 1 0 00-.364 1.118l1.287 3.957c.3.921-.755 1.688-1.54 1.118l-3.37-2.448a1 1 0 00-1.176 0l-3.37 2.448c-.784.57-1.838-.197-1.539-1.118l1.287-3.957a1 1 0 00-.364-1.118L2.063 9.384c-.783-.57-.38-1.81.588-1.81h4.162a1 1 0 00.95-.69l1.286-3.957z" />
        </svg>
      ))}
    </span>
  );
}

function localized(v: VenueDetail, field: "review" | "accessibility", lang: string): string {
  const langField = `${field}_${lang}` as keyof VenueDetail;
  const fallback = `${field}_en` as keyof VenueDetail;
  return (v[langField] as string) || (v[fallback] as string) || "";
}

function formatKickoff(iso: string, locale: string): string {
  try {
    const d = new Date(iso);
    return new Intl.DateTimeFormat(locale, {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short",
    }).format(d);
  } catch {
    return iso;
  }
}

function VenueMatchRow({
  m,
  locale,
  t,
}: {
  m: VenueScheduledMatch;
  locale: string;
  t: (key: string, opts?: Record<string, string | number>) => string;
}) {
  const home = m.home_team_name
    ? localizedTeamName(m.home_team_code, m.home_team_name, locale)
    : t("venues.tbd");
  const away = m.away_team_name
    ? localizedTeamName(m.away_team_code, m.away_team_name, locale)
    : t("venues.tbd");
  const stage = t(`venues.stages.${m.stage}`, {
    defaultValue: formatStageSlugSpacesOnly(m.stage),
  });
  const groupHint =
    m.stage === "group" && m.group_letter
      ? ` · ${t("venues.groupLetter", { letter: m.group_letter })}`
      : "";

  return (
    <li className="border-b border-gray-100 last:border-0 py-3 first:pt-0">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="text-xs text-gray-500 mb-0.5">
            {t("venues.matchNumber", { n: m.match_number })}
            <span className="text-gray-400">
              {" "}
              · {stage}
              {groupHint}
            </span>
          </div>
          <div className="text-sm font-medium text-gray-900">
            {home} <span className="text-gray-400 font-normal">{t("common.vs")}</span> {away}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            <span className="font-medium text-gray-600">{t("venues.kickoff")}:</span>{" "}
            {formatKickoff(m.kickoff_utc, locale)}
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-[10px] uppercase tracking-wide text-gray-400 mb-0.5">
            {t("venues.fixtureHype")}
          </div>
          <Stars count={m.attractiveness_stars} />
        </div>
      </div>
    </li>
  );
}

export default function Venues() {
  const { t, i18n } = useTranslation();
  const [venues, setVenues] = useState<VenueDetail[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<VenueDetail[]>("/venues")
      .then((r) => setVenues(r.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <h1 className="text-2xl sm:text-3xl font-bold mb-6 sm:mb-8">{t("venues.title")}</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        {venues.map((v) => (
          <div
            key={v.id}
            className="bg-white rounded-xl shadow-md overflow-hidden flex flex-col"
          >
            {v.image_url && (
              <div className="h-48 overflow-hidden">
                <img
                  src={v.image_url}
                  alt={v.name}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              </div>
            )}

            <div className="p-5 flex-1 flex flex-col min-h-0">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h2 className="text-lg font-bold text-gray-900">{v.name}</h2>
                  <p className="text-sm text-gray-500">
                    {v.city}, {localizedVenueCountry(v.country, i18n.language)}
                  </p>
                </div>
                {v.rating && <Stars count={v.rating} />}
              </div>

              <div className="grid grid-cols-3 gap-3 text-sm mb-4">
                <div className="bg-gray-50 rounded-lg p-2 text-center">
                  <div className="text-xs text-gray-500">{t("venues.yearBuilt")}</div>
                  <div className="font-semibold">{v.year_built || "—"}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-2 text-center">
                  <div className="text-xs text-gray-500">{t("venues.capacity")}</div>
                  <div className="font-semibold">{v.capacity.toLocaleString()}</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-2 text-center">
                  <div className="text-xs text-gray-500">{t("venues.expectedTemp")}</div>
                  <div className="font-semibold">
                    {v.expected_temp_celsius !== null ? `${v.expected_temp_celsius}°C` : "—"}
                  </div>
                </div>
              </div>

              <div className="mb-4 border border-gray-100 rounded-lg bg-gray-50/50 flex flex-col max-h-80 min-h-0">
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide px-3 pt-3 pb-2 border-b border-gray-100 bg-white/60">
                  {t("venues.schedule")}
                </h3>
                {v.matches?.length ? (
                  <ul className="px-3 overflow-y-auto flex-1">
                    {v.matches.map((m) => (
                      <VenueMatchRow key={m.match_id} m={m} locale={i18n.language} t={t} />
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500 px-3 py-4">{t("venues.noMatches")}</p>
                )}
              </div>

              {v.city_attractiveness && (
                <div className="flex items-center gap-2 mb-3 text-sm">
                  <span className="text-gray-500">{t("venues.cityAttractiveness")}:</span>
                  <Stars count={v.city_attractiveness} />
                </div>
              )}

              <div className="mb-3">
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                  {t("venues.review")}
                </h3>
                <p className="text-sm text-gray-700 leading-relaxed">
                  {localized(v, "review", i18n.language)}
                </p>
              </div>

              <div className="mt-auto pt-3 border-t">
                <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                  {t("venues.accessibility")}
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {localized(v, "accessibility", i18n.language)}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
