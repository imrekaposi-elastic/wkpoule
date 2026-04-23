import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { AdminUserRow } from "../types";

const LOCALE_MAP: Record<string, string> = {
  en: "en-US",
  nl: "nl-NL",
  pt: "pt-BR",
  de: "de-DE",
  he: "he-IL",
};

export default function AdminSettings() {
  const { t, i18n } = useTranslation();
  const { user, refreshUser } = useAuth();
  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [banner, setBanner] = useState<{ ok: boolean; text: string } | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [roleUpdatingId, setRoleUpdatingId] = useState<number | null>(null);

  const locale = LOCALE_MAP[i18n.language] || "en-US";

  const load = useCallback(() => {
    setLoading(true);
    api
      .get<AdminUserRow[]>("/admin/users")
      .then((r) => setRows(r.data))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const adminCount = rows.filter((r) => r.is_admin).length;

  const onRoleChange = async (u: AdminUserRow, makeAdmin: boolean) => {
    if (makeAdmin) {
      if (!window.confirm(t("adminSettings.confirmPromote", { username: u.username }))) {
        return;
      }
    } else {
      if (!window.confirm(t("adminSettings.confirmDemote", { username: u.username }))) {
        return;
      }
    }
    setRoleUpdatingId(u.id);
    setBanner(null);
    try {
      const { data } = await api.patch<AdminUserRow>(`/admin/users/${u.id}`, {
        is_admin: makeAdmin,
      });
      setRows((prev) => prev.map((row) => (row.id === data.id ? data : row)));
      setBanner({
        ok: true,
        text: makeAdmin
          ? t("adminSettings.promoted", { username: u.username })
          : t("adminSettings.demoted", { username: u.username }),
      });
      if (u.id === user?.id) {
        await refreshUser();
      }
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail;
      setBanner({
        ok: false,
        text:
          typeof detail === "string"
            ? detail
            : t("adminSettings.roleUpdateFailed"),
      });
    } finally {
      setRoleUpdatingId(null);
    }
  };

  const onDelete = async (u: AdminUserRow) => {
    if (u.id === user?.id) return;
    if (
      !window.confirm(
        t("adminSettings.confirmDelete", { username: u.username })
      )
    ) {
      return;
    }
    setDeletingId(u.id);
    setBanner(null);
    try {
      await api.delete(`/admin/users/${u.id}`);
      setBanner({ ok: true, text: t("adminSettings.deleted", { username: u.username }) });
      setRows((prev) => prev.filter((x) => x.id !== u.id));
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail;
      setBanner({
        ok: false,
        text:
          typeof detail === "string"
            ? detail
            : t("adminSettings.deleteFailed"),
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
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-pitch-900 mb-2">
        {t("adminSettings.title")}
      </h1>
      <p className="text-sm text-gray-600 mb-6">{t("adminSettings.intro")}</p>

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

      <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b bg-gray-50">
                <th className="py-3 px-4 font-medium">{t("adminSettings.colUser")}</th>
                <th className="py-3 px-4 font-medium">{t("adminSettings.colEmail")}</th>
                <th className="py-3 px-4 font-medium">{t("adminSettings.colRole")}</th>
                <th className="py-3 px-4 font-medium">{t("adminSettings.colJoined")}</th>
                <th className="py-3 px-4 font-medium text-right">
                  {t("adminSettings.colActions")}
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((u) => {
                const isSelf = u.id === user?.id;
                return (
                  <tr key={u.id} className="border-b last:border-0 hover:bg-gray-50/80">
                    <td className="py-3 px-4 font-medium text-gray-900">
                      {u.username}
                      {isSelf && (
                        <span className="ml-2 text-xs font-normal text-pitch-600">
                          ({t("adminSettings.you")})
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-gray-700">{u.email}</td>
                    <td className="py-3 px-4">
                      {u.is_admin ? (
                        <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-900">
                          {t("adminSettings.roleAdmin")}
                        </span>
                      ) : (
                        <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                          {t("adminSettings.rolePlayer")}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-gray-600 whitespace-nowrap">
                      {new Date(u.created_at).toLocaleString(locale, {
                        dateStyle: "medium",
                        timeStyle: "short",
                      })}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      {u.is_admin ? (
                        <button
                          type="button"
                          disabled={
                            adminCount < 2 ||
                            roleUpdatingId === u.id ||
                            deletingId === u.id
                          }
                          title={
                            adminCount < 2
                              ? t("adminSettings.cannotDemoteLastAdmin")
                              : undefined
                          }
                          onClick={() => onRoleChange(u, false)}
                          className="text-sm text-amber-800 hover:text-amber-950 font-medium disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          {roleUpdatingId === u.id
                            ? t("adminSettings.roleUpdating")
                            : t("adminSettings.demote")}
                        </button>
                      ) : (
                        <button
                          type="button"
                          disabled={roleUpdatingId === u.id || deletingId === u.id}
                          onClick={() => onRoleChange(u, true)}
                          className="text-sm text-pitch-700 hover:text-pitch-900 font-medium disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          {roleUpdatingId === u.id
                            ? t("adminSettings.roleUpdating")
                            : t("adminSettings.promote")}
                        </button>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        type="button"
                        disabled={isSelf || deletingId === u.id}
                        onClick={() => onDelete(u)}
                        className="text-sm text-red-700 hover:text-red-900 font-medium disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {deletingId === u.id
                          ? t("adminSettings.deleting")
                          : t("adminSettings.delete")}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
