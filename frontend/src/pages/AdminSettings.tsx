import { Fragment, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import { resolveLocale } from "../i18n/languages";
import type { AdminUserRow } from "../types";

function parseApiDetail(err: unknown): string | undefined {
  const raw = (err as { response?: { data?: { detail?: unknown } } })?.response?.data
    ?.detail;
  if (typeof raw === "string") return raw;
  if (Array.isArray(raw)) {
    const msgs = raw
      .map((item) =>
        typeof item === "object" && item !== null && "msg" in item
          ? String((item as { msg: string }).msg)
          : null
      )
      .filter(Boolean) as string[];
    if (msgs.length) return msgs.join(" ");
  }
  return undefined;
}

export default function AdminSettings() {
  const { t, i18n } = useTranslation();
  const { user, refreshUser } = useAuth();
  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [banner, setBanner] = useState<{ ok: boolean; text: string } | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [roleUpdatingId, setRoleUpdatingId] = useState<number | null>(null);
  const [passwordResetFor, setPasswordResetFor] = useState<number | null>(null);
  const [resetPw1, setResetPw1] = useState("");
  const [resetPw2, setResetPw2] = useState("");
  const [passwordResetSavingId, setPasswordResetSavingId] = useState<number | null>(
    null
  );

  const locale = resolveLocale(i18n.language);

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
      setBanner({
        ok: false,
        text: parseApiDetail(err) ?? t("adminSettings.roleUpdateFailed"),
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
      setBanner({
        ok: false,
        text: parseApiDetail(err) ?? t("adminSettings.deleteFailed"),
      });
    } finally {
      setDeletingId(null);
    }
  };

  const togglePasswordReset = (u: AdminUserRow) => {
    setBanner(null);
    if (passwordResetFor === u.id) {
      setPasswordResetFor(null);
      setResetPw1("");
      setResetPw2("");
    } else {
      setPasswordResetFor(u.id);
      setResetPw1("");
      setResetPw2("");
    }
  };

  const onSubmitPasswordReset = async (u: AdminUserRow) => {
    setBanner(null);
    if (resetPw1 !== resetPw2) {
      setBanner({ ok: false, text: t("register.passwordsMismatch") });
      return;
    }
    if (resetPw1.length < 8) {
      setBanner({ ok: false, text: t("adminSettings.passwordTooShort") });
      return;
    }
    setPasswordResetSavingId(u.id);
    try {
      await api.post(`/admin/users/${u.id}/password`, {
        new_password: resetPw1,
      });
      setPasswordResetFor(null);
      setResetPw1("");
      setResetPw2("");
      const msg =
        u.id === user?.id
          ? `${t("adminSettings.resetPasswordSuccess", { username: u.username })} ${t("adminSettings.selfPasswordNote")}`
          : t("adminSettings.resetPasswordSuccess", { username: u.username });
      setBanner({ ok: true, text: msg });
    } catch (err: unknown) {
      setBanner({
        ok: false,
        text: parseApiDetail(err) ?? t("adminSettings.resetPasswordFailed"),
      });
    } finally {
      setPasswordResetSavingId(null);
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
    <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6 py-6 sm:py-8">
      <h1 className="text-2xl sm:text-3xl font-bold text-pitch-900 mb-2">
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
        <div className="overflow-x-auto overscroll-x-contain">
          <table className="w-full text-sm min-w-[64rem]">
            <thead>
              <tr className="text-left text-gray-500 border-b bg-gray-50">
                <th className="py-3 px-4 font-medium w-[14rem]">{t("adminSettings.colUser")}</th>
                <th className="py-3 px-4 font-medium min-w-[18rem]">{t("adminSettings.colEmail")}</th>
                <th className="py-3 px-4 font-medium">{t("adminSettings.colLanguage")}</th>
                <th className="py-3 px-4 font-medium">{t("adminSettings.colRole")}</th>
                <th className="py-3 px-4 font-medium">{t("adminSettings.colJoined")}</th>
                <th className="py-3 px-4 font-medium text-right">
                  {t("adminSettings.colRoleActions")}
                </th>
                <th className="py-3 px-4 font-medium text-right">
                  {t("adminSettings.colResetPassword")}
                </th>
                <th className="py-3 px-4 font-medium text-right">
                  {t("adminSettings.colActions")}
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((u) => {
                const isSelf = u.id === user?.id;
                const busy =
                  roleUpdatingId === u.id ||
                  deletingId === u.id ||
                  passwordResetSavingId === u.id;
                return (
                  <Fragment key={u.id}>
                    <tr className="border-b last:border-0 hover:bg-gray-50/80">
                      <td className="py-3 px-4 font-medium text-gray-900 break-words">
                        {u.username}
                        {isSelf && (
                          <span className="ml-2 text-xs font-normal text-pitch-600">
                            ({t("adminSettings.you")})
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-gray-700 break-all">{u.email}</td>
                      <td className="py-3 px-4 text-gray-600 font-mono text-xs uppercase">
                        {u.preferred_language}
                      </td>
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
                            disabled={adminCount < 2 || busy}
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
                            disabled={busy}
                            onClick={() => onRoleChange(u, true)}
                            className="text-sm text-pitch-700 hover:text-pitch-900 font-medium disabled:opacity-40 disabled:cursor-not-allowed"
                          >
                            {roleUpdatingId === u.id
                              ? t("adminSettings.roleUpdating")
                              : t("adminSettings.promote")}
                          </button>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => togglePasswordReset(u)}
                          className="text-sm text-gray-800 hover:text-gray-950 font-medium disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          {passwordResetFor === u.id
                            ? t("adminSettings.resetPasswordClose")
                            : t("adminSettings.resetPasswordOpen")}
                        </button>
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <button
                          type="button"
                          disabled={isSelf || busy}
                          onClick={() => onDelete(u)}
                          className="text-sm text-red-700 hover:text-red-900 font-medium disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          {deletingId === u.id
                            ? t("adminSettings.deleting")
                            : t("adminSettings.delete")}
                        </button>
                      </td>
                    </tr>
                    {passwordResetFor === u.id && (
                      <tr className="border-b bg-gray-50/90">
                        <td colSpan={8} className="py-4 px-4">
                          <p className="text-xs text-gray-600 mb-3 max-w-xl">
                            {t("adminSettings.resetPasswordHint")}
                          </p>
                          <div className="flex flex-col sm:flex-row sm:flex-wrap gap-3 sm:items-end max-w-2xl">
                            <label className="flex flex-col gap-1 text-xs text-gray-600 flex-1 min-w-[10rem]">
                              {t("register.password")}
                              <input
                                type="password"
                                autoComplete="new-password"
                                value={resetPw1}
                                onChange={(e) => setResetPw1(e.target.value)}
                                className="rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-900"
                              />
                            </label>
                            <label className="flex flex-col gap-1 text-xs text-gray-600 flex-1 min-w-[10rem]">
                              {t("register.confirmPassword")}
                              <input
                                type="password"
                                autoComplete="new-password"
                                value={resetPw2}
                                onChange={(e) => setResetPw2(e.target.value)}
                                className="rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-900"
                              />
                            </label>
                            <div className="flex gap-2 pb-0.5">
                              <button
                                type="button"
                                disabled={passwordResetSavingId === u.id}
                                onClick={() => onSubmitPasswordReset(u)}
                                className="rounded-md bg-pitch-700 text-white text-sm font-medium px-3 py-1.5 hover:bg-pitch-800 disabled:opacity-40"
                              >
                                {passwordResetSavingId === u.id
                                  ? t("adminSettings.resetPasswordSaving")
                                  : t("adminSettings.resetPasswordApply")}
                              </button>
                              <button
                                type="button"
                                disabled={passwordResetSavingId === u.id}
                                onClick={() => togglePasswordReset(u)}
                                className="rounded-md border border-gray-300 text-sm font-medium px-3 py-1.5 text-gray-800 hover:bg-gray-100 disabled:opacity-40"
                              >
                                {t("adminSettings.resetPasswordClose")}
                              </button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
