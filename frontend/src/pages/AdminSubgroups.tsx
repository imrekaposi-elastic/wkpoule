import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { resolveLocale } from "../i18n/languages";
import type { AdminSubgroupRow } from "../types";

export default function AdminSubgroups() {
  const { t, i18n } = useTranslation();
  const [rows, setRows] = useState<AdminSubgroupRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [banner, setBanner] = useState<{ ok: boolean; text: string } | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const locale = resolveLocale(i18n.language);

  const load = useCallback(() => {
    setLoading(true);
    api
      .get<AdminSubgroupRow[]>("/admin/subgroups")
      .then((r) => setRows(r.data))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onDeleteEmpty = async (sg: AdminSubgroupRow) => {
    if (sg.member_count > 0) return;
    if (!window.confirm(t("adminSubgroups.confirmDeleteEmpty", { name: sg.name }))) return;
    setDeletingId(sg.id);
    setBanner(null);
    try {
      await api.delete(`/admin/subgroups/${sg.id}`);
      setBanner({ ok: true, text: t("adminSubgroups.deletedEmpty", { name: sg.name }) });
      load();
      window.dispatchEvent(new Event("subgroups-invites-changed"));
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail;
      setBanner({
        ok: false,
        text: typeof detail === "string" ? detail : t("adminSubgroups.deleteFailed"),
      });
    } finally {
      setDeletingId(null);
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
    <div className="max-w-5xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-pitch-900 mb-2">{t("adminSubgroups.title")}</h1>
      <p className="text-sm text-gray-600 mb-6">{t("adminSubgroups.intro")}</p>

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

      <div className="space-y-6">
        {rows.map((sg) => (
          <div
            key={sg.id}
            className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden"
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 px-4 py-3 bg-gray-50 border-b border-gray-100">
              <div>
                <h2 className="font-semibold text-pitch-900">{sg.name}</h2>
                <p className="text-xs text-gray-500">
                  ID {sg.id} · {t("adminSubgroups.memberCount", { count: sg.member_count })} ·{" "}
                  {new Date(sg.created_at).toLocaleString(locale, {
                    dateStyle: "medium",
                    timeStyle: "short",
                  })}
                </p>
              </div>
              <button
                type="button"
                disabled={sg.member_count > 0 || deletingId === sg.id}
                title={
                  sg.member_count > 0 ? t("adminSubgroups.deleteOnlyWhenEmpty") : undefined
                }
                onClick={() => onDeleteEmpty(sg)}
                className="text-sm text-red-700 border border-red-200 px-3 py-1.5 rounded-lg hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {deletingId === sg.id ? t("adminSubgroups.deleting") : t("adminSubgroups.deleteEmpty")}
              </button>
            </div>
            {sg.members.length === 0 ? (
              <p className="text-sm text-gray-500 px-4 py-3">{t("adminSubgroups.noMembers")}</p>
            ) : (
              <ul className="divide-y divide-gray-100 text-sm">
                {sg.members.map((m) => (
                  <li key={m.user_id} className="px-4 py-2 flex justify-between gap-2">
                    <span className="font-medium text-gray-900">{m.username}</span>
                    <span className="text-gray-500 text-xs shrink-0">
                      {m.role === "admin"
                        ? t("subgroups.roleAdmin")
                        : t("subgroups.roleMember")}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>

      {rows.length === 0 && (
        <p className="text-gray-500 text-sm text-center py-8">{t("adminSubgroups.none")}</p>
      )}
    </div>
  );
}
