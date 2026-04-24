import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import type { SubgroupInvitePending, SubgroupMine } from "../types";

export default function Subgroups() {
  const { t } = useTranslation();
  const [mine, setMine] = useState<SubgroupMine[]>([]);
  const [pending, setPending] = useState<SubgroupInvitePending[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [banner, setBanner] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.get<SubgroupMine[]>("/subgroups/mine"),
      api.get<SubgroupInvitePending[]>("/subgroups/invites/pending"),
    ])
      .then(([m, p]) => {
        setMine(m.data);
        setPending(p.data);
      })
      .catch(() => {
        setMine([]);
        setPending([]);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const tmr = window.setInterval(() => {
      api
        .get<SubgroupMine[]>("/subgroups/mine")
        .then((r) => setMine(r.data))
        .catch(() => {});
    }, 30000);
    const onMineChanged = () => {
      api
        .get<SubgroupMine[]>("/subgroups/mine")
        .then((r) => setMine(r.data))
        .catch(() => {});
    };
    window.addEventListener("subgroups-mine-changed", onMineChanged);
    return () => {
      window.clearInterval(tmr);
      window.removeEventListener("subgroups-mine-changed", onMineChanged);
    };
  }, []);

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const n = name.trim();
    if (!n) return;
    setCreating(true);
    setBanner(null);
    try {
      await api.post("/subgroups", { name: n });
      setName("");
      setBanner({ ok: true, text: t("subgroups.created") });
      load();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail;
      setBanner({
        ok: false,
        text: typeof detail === "string" ? detail : t("subgroups.createFailed"),
      });
    } finally {
      setCreating(false);
    }
  };

  const onAccept = async (inviteId: number) => {
    setBanner(null);
    try {
      await api.post(`/subgroups/invites/${inviteId}/accept`);
      setBanner({ ok: true, text: t("subgroups.inviteAccepted") });
      load();
      window.dispatchEvent(new Event("subgroups-invites-changed"));
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail;
      setBanner({
        ok: false,
        text: typeof detail === "string" ? detail : t("subgroups.inviteAcceptFailed"),
      });
    }
  };

  const onDecline = async (inviteId: number) => {
    try {
      await api.post(`/subgroups/invites/${inviteId}/decline`);
      load();
      window.dispatchEvent(new Event("subgroups-invites-changed"));
    } catch {
      /* ignore */
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-pitch-900 mb-2">{t("subgroups.title")}</h1>
      <p className="text-sm text-gray-600 mb-6">{t("subgroups.intro")}</p>

      {banner && (
        <div
          className={`mb-4 px-4 py-3 rounded-lg text-sm ${
            banner.ok
              ? "bg-emerald-50 text-emerald-900 border border-emerald-200"
              : "bg-red-50 text-red-900 border border-red-200"
          }`}
        >
          {banner.text}
        </div>
      )}

      <section className="mb-10 bg-white rounded-xl shadow-md border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-pitch-800 mb-3">{t("subgroups.addSubgroup")}</h2>
        <form onSubmit={onCreate} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={t("subgroups.namePlaceholder")}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
            maxLength={120}
          />
          <button
            type="submit"
            disabled={creating || !name.trim()}
            className="bg-pitch-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-pitch-800 disabled:opacity-50"
          >
            {creating ? t("subgroups.creating") : t("subgroups.create")}
          </button>
        </form>
      </section>

      {pending.length > 0 && (
        <section className="mb-10">
          <h2 className="text-lg font-semibold text-pitch-800 mb-3">
            {t("subgroups.pendingInvites")}
          </h2>
          <ul className="space-y-3">
            {pending.map((inv) => (
              <li
                key={inv.id}
                className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
              >
                <div>
                  <p className="font-medium text-amber-950">{inv.subgroup_name}</p>
                  <p className="text-xs text-amber-900/80">{t("subgroups.invitedAs", { email: inv.email })}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => onAccept(inv.id)}
                    className="text-sm bg-pitch-700 text-white px-3 py-1.5 rounded-md hover:bg-pitch-800"
                  >
                    {t("subgroups.accept")}
                  </button>
                  <button
                    type="button"
                    onClick={() => onDecline(inv.id)}
                    className="text-sm border border-gray-300 px-3 py-1.5 rounded-md hover:bg-gray-50"
                  >
                    {t("subgroups.decline")}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold text-pitch-800 mb-3">{t("subgroups.mySubgroups")}</h2>
        {mine.length === 0 ? (
          <p className="text-gray-500 text-sm">{t("subgroups.noneYet")}</p>
        ) : (
          <ul className="space-y-2">
            {mine.map((s) => (
              <li key={s.id}>
                <Link
                  to={`/subgroups/${s.id}`}
                  className="flex items-center justify-between gap-3 bg-white rounded-lg border border-gray-100 shadow-sm px-4 py-3 hover:border-pitch-300 transition-colors"
                >
                  <span>
                    <span className="font-medium text-pitch-900">{s.name}</span>
                    <span className="text-sm text-gray-500 ml-2">
                      ({s.member_count} ·{" "}
                      {s.my_role === "admin" ? t("subgroups.roleAdmin") : t("subgroups.roleMember")})
                    </span>
                  </span>
                  {(s.unread_message_count ?? 0) > 0 && (
                    <span
                      className="shrink-0 min-w-[1.35rem] h-6 px-1.5 flex items-center justify-center rounded-full bg-sky-600 text-white text-xs font-bold"
                      title={t("subgroups.unreadChatBadge", { count: s.unread_message_count })}
                    >
                      {(s.unread_message_count ?? 0) > 99 ? "99+" : s.unread_message_count}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
