import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import ExpertAvatar, { EXPERT_STYLE_KEYS } from "../components/ExpertAvatar";

const FEATURE_KEYS = ["venues", "analysis", "helper", "subleague", "chat"] as const;

export default function LandingPage() {
  const { t } = useTranslation();
  const featuredExperts = EXPERT_STYLE_KEYS;

  return (
    <div className="bg-gradient-to-b from-pitch-900 via-pitch-900 to-gray-50 text-white">
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute -left-16 top-20 h-64 w-64 rounded-full bg-green-400 blur-3xl" />
          <div className="absolute right-0 top-8 h-80 w-80 rounded-full bg-yellow-300 blur-3xl" />
          <div className="absolute bottom-0 left-1/2 h-72 w-72 rounded-full bg-sky-400 blur-3xl" />
        </div>

        <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:py-24">
          <div className="flex flex-col justify-center">
            <p className="mb-4 inline-flex w-fit rounded-full bg-white/10 px-3 py-1 text-sm font-medium text-green-100 ring-1 ring-white/20">
              {t("landing.kicker")}
            </p>
            <h1 className="max-w-3xl text-4xl font-black tracking-tight sm:text-5xl lg:text-6xl">
              {t("landing.heroTitle")}
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-green-50/90">
              {t("landing.heroSubtitle")}
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                to="/register"
                className="rounded-xl bg-yellow-300 px-6 py-3 text-center font-bold text-pitch-900 shadow-lg shadow-yellow-900/20 transition hover:bg-yellow-200"
              >
                {t("landing.registerCta")}
              </Link>
              <Link
                to="/login"
                className="rounded-xl border border-white/25 bg-white/10 px-6 py-3 text-center font-bold text-white transition hover:bg-white/20"
              >
                {t("landing.loginCta")}
              </Link>
            </div>
          </div>

          <div className="overflow-hidden rounded-[2rem] border border-white/15 shadow-2xl ring-1 ring-white/10">
            <div className="relative">
              <img
                src="/images/world-cup-2026-begun.png"
                alt={t("landing.worldCupBegunAlt")}
                className="block h-auto w-full object-cover"
              />
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-pitch-950 via-pitch-950/85 to-transparent px-6 pb-6 pt-16 sm:px-8 sm:pb-8">
                <p className="text-center text-2xl font-black tracking-tight text-white drop-shadow-lg sm:text-3xl lg:text-4xl">
                  {t("landing.worldCupBegun")}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-gray-50 px-4 py-14 text-gray-900 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-bold uppercase tracking-[0.25em] text-pitch-700">
              {t("landing.featuresKicker")}
            </p>
            <h2 className="mt-3 text-3xl font-black sm:text-4xl">{t("landing.featuresTitle")}</h2>
          </div>
          <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-5">
            {FEATURE_KEYS.map((key) => (
              <div key={key} className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-pitch-700 text-xl text-white">
                  {t(`landing.features.${key}.icon`)}
                </div>
                <h3 className="font-bold text-pitch-900">{t(`landing.features.${key}.title`)}</h3>
                <p className="mt-2 text-sm leading-6 text-gray-600">
                  {t(`landing.features.${key}.text`)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-white px-4 py-14 text-gray-900 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.25em] text-pitch-700">
                {t("landing.expertsKicker")}
              </p>
              <h2 className="mt-3 text-3xl font-black sm:text-4xl">{t("landing.expertsTitle")}</h2>
              <p className="mt-3 max-w-2xl text-gray-600">{t("landing.expertsText")}</p>
            </div>
          </div>

          <div className="mt-9 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7">
            {featuredExperts.map((styleKey) => {
              const label = t(`matchDetail.styles.${styleKey}`, styleKey);
              return (
                <div
                  key={styleKey}
                  className="flex flex-col items-center rounded-3xl bg-gradient-to-b from-yellow-50 to-white p-4 text-center shadow-sm ring-1 ring-yellow-100"
                >
                  <ExpertAvatar styleKey={styleKey} label={label} size="lg" />
                  <p className="mt-3 text-sm font-bold text-pitch-900">{label}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="bg-pitch-900 px-4 py-14 sm:px-6">
        <div className="mx-auto flex max-w-5xl flex-col items-center rounded-[2rem] bg-white p-8 text-center text-gray-900 shadow-2xl sm:p-10">
          <h2 className="text-3xl font-black sm:text-4xl">{t("landing.finalTitle")}</h2>
          <p className="mt-3 max-w-2xl text-gray-600">{t("landing.finalText")}</p>
          <div className="mt-7 flex flex-col gap-3 sm:flex-row">
            <Link
              to="/register"
              className="rounded-xl bg-pitch-700 px-6 py-3 font-bold text-white transition hover:bg-pitch-800"
            >
              {t("landing.registerCta")}
            </Link>
            <Link
              to="/login"
              className="rounded-xl border border-gray-300 px-6 py-3 font-bold text-pitch-800 transition hover:bg-gray-50"
            >
              {t("landing.loginCta")}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
