import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import Pagination from "../components/Pagination";
import { useAuth } from "../context/AuthContext";
import { resolveLocale } from "../i18n/languages";
import type { SubgroupDetail as SubgroupDetailType, SubgroupMessage } from "../types";
import { normalizeRankingsResponse, rankingsItems } from "../utils/rankings";

const AVATAR_PALETTE = [
  "bg-emerald-600",
  "bg-sky-600",
  "bg-violet-600",
  "bg-amber-600",
  "bg-rose-600",
  "bg-teal-600",
  "bg-indigo-600",
  "bg-orange-600",
] as const;

function avatarInitials(username: string): string {
  const parts = username.trim().split(/[\s._-]+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return username.slice(0, 2).toUpperCase();
}

function avatarColorClass(username: string): (typeof AVATAR_PALETTE)[number] {
  let hash = 0;
  for (let i = 0; i < username.length; i += 1) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash);
  }
  return AVATAR_PALETTE[Math.abs(hash) % AVATAR_PALETTE.length];
}

function formatChatTimestamp(iso: string, locale: string): string {
  const date = new Date(iso);
  const now = new Date();
  const sameDay =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();
  return date.toLocaleString(locale, sameDay ? { timeStyle: "short" } : { dateStyle: "short", timeStyle: "short" });
}

export default function SubgroupDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const [detail, setDetail] = useState<SubgroupDetailType | null>(null);
  const [messages, setMessages] = useState<SubgroupMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [msgBody, setMsgBody] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [banner, setBanner] = useState<{ ok: boolean; text: string } | null>(null);
  const [rankingsPage, setRankingsPage] = useState(1);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const subgroupId = id ? parseInt(id, 10) : NaN;

  const loadMessages = useCallback(() => {
    if (Number.isNaN(subgroupId)) return;
    api
      .get<SubgroupMessage[]>(`/subgroups/${subgroupId}/messages`)
      .then((r) => {
        setMessages(r.data);
        window.dispatchEvent(new Event("subgroups-mine-changed"));
      })
      .catch(() => setMessages([]));
  }, [subgroupId]);

  const loadDetail = useCallback(
    (page: number) => {
      if (Number.isNaN(subgroupId)) return;
      api
        .get<SubgroupDetailType>(`/subgroups/${subgroupId}`, {
          params: { page, page_size: 20 },
        })
        .then((r) =>
          setDetail({
            ...r.data,
            rankings: normalizeRankingsResponse(r.data.rankings),
          }),
        )
        .catch(() => setDetail(null));
    },
    [subgroupId],
  );

  useEffect(() => {
    if (Number.isNaN(subgroupId)) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      api.get<SubgroupDetailType>(`/subgroups/${subgroupId}`, {
        params: { page: rankingsPage, page_size: 20 },
      }),
      api.get<SubgroupMessage[]>(`/subgroups/${subgroupId}/messages`),
    ])
      .then(([d, m]) => {
        setDetail({
          ...d.data,
          rankings: normalizeRankingsResponse(d.data.rankings),
        });
        setMessages(m.data);
        window.dispatchEvent(new Event("subgroups-mine-changed"));
      })
      .catch(() => {
        setDetail(null);
        setMessages([]);
      })
      .finally(() => setLoading(false));
  }, [subgroupId, rankingsPage]);

  useEffect(() => {
    if (Number.isNaN(subgroupId) || !detail) return;
    const tmr = window.setInterval(loadMessages, 12000);
    return () => window.clearInterval(tmr);
  }, [subgroupId, detail, loadMessages]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const onLeave = async () => {
    if (!window.confirm(t("subgroups.confirmLeave"))) return;
    try {
      await api.post(`/subgroups/${subgroupId}/leave`);
      window.dispatchEvent(new Event("subgroups-invites-changed"));
      navigate("/subgroups");
    } catch (err: unknown) {
      const detailErr = (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail;
      setBanner({
        ok: false,
        text: typeof detailErr === "string" ? detailErr : t("subgroups.leaveFailed"),
      });
    }
  };

  const onDeleteSubgroup = async () => {
    if (!window.confirm(t("subgroups.confirmDeleteSubgroup"))) return;
    try {
      await api.delete(`/subgroups/${subgroupId}`);
      window.dispatchEvent(new Event("subgroups-invites-changed"));
      navigate("/subgroups");
    } catch (err: unknown) {
      const detailErr = (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail;
      setBanner({
        ok: false,
        text: typeof detailErr === "string" ? detailErr : t("subgroups.deleteSubgroupFailed"),
      });
    }
  };

  const onInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    const em = inviteEmail.trim();
    if (!em) return;
    setSending(true);
    setBanner(null);
    try {
      await api.post(`/subgroups/${subgroupId}/invites`, { email: em });
      setInviteEmail("");
      setBanner({ ok: true, text: t("subgroups.inviteSent") });
      window.dispatchEvent(new Event("subgroups-invites-changed"));
    } catch (err: unknown) {
      const detailErr = (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail;
      setBanner({
        ok: false,
        text: typeof detailErr === "string" ? detailErr : t("subgroups.inviteFailed"),
      });
    } finally {
      setSending(false);
    }
  };

  const onSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const b = msgBody.trim();
    if (!b) return;
    try {
      await api.post(`/subgroups/${subgroupId}/messages`, { body: b });
      setMsgBody("");
      loadMessages();
    } catch {
      /* ignore */
    }
  };

  const onDeleteMessage = async (messageId: number) => {
    if (!window.confirm(t("subgroups.confirmDeleteMessage"))) return;
    try {
      await api.delete(`/subgroups/${subgroupId}/messages/${messageId}`);
      loadMessages();
    } catch {
      /* ignore */
    }
  };

  const onRemoveMember = async (memberUserId: number, username: string) => {
    if (!window.confirm(t("subgroups.confirmRemoveMember", { username }))) return;
    setBanner(null);
    try {
      await api.delete(`/subgroups/${subgroupId}/members/${memberUserId}`);
      setBanner({ ok: true, text: t("subgroups.memberRemoved", { username }) });
      loadDetail(rankingsPage);
      loadMessages();
      window.dispatchEvent(new Event("subgroups-invites-changed"));
    } catch (err: unknown) {
      const detailErr = (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail;
      setBanner({
        ok: false,
        text: typeof detailErr === "string" ? detailErr : t("subgroups.removeMemberFailed"),
      });
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pitch-600" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-8">
        <p className="text-red-700">{t("subgroups.notFound")}</p>
        <Link to="/subgroups" className="text-pitch-700 text-sm mt-2 inline-block">
          {t("subgroups.backToList")}
        </Link>
      </div>
    );
  }

  const locale = resolveLocale(i18n.language);

  return (
    <div className="max-w-4xl mx-auto px-3 sm:px-4 py-6 sm:py-8">
      <div className="mb-4">
        <Link to="/subgroups" className="text-sm text-pitch-700 hover:underline">
          {t("subgroups.backToList")}
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-pitch-900 break-words">{detail.name}</h1>
          <p className="text-sm text-gray-600 mt-1">
            {detail.my_role === "admin" ? t("subgroups.roleAdmin") : t("subgroups.roleMember")}
          </p>
        </div>
        {detail.my_role === "admin" ? (
          <button
            type="button"
            onClick={onDeleteSubgroup}
            className="text-sm text-white bg-red-700 border border-red-800 px-3 py-1.5 rounded-lg hover:bg-red-800"
          >
            {t("subgroups.deleteSubgroup")}
          </button>
        ) : (
          <button
            type="button"
            onClick={onLeave}
            className="text-sm text-red-700 border border-red-200 px-3 py-1.5 rounded-lg hover:bg-red-50"
          >
            {t("subgroups.leave")}
          </button>
        )}
      </div>

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

      {detail.my_role === "admin" && (
        <section className="mb-8 bg-white rounded-xl shadow-md border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-pitch-800 mb-2">{t("subgroups.inviteByEmail")}</h2>
          <p className="text-xs text-gray-500 mb-3">{t("subgroups.inviteHelp")}</p>
          <form onSubmit={onInvite} className="flex flex-col sm:flex-row gap-2">
            <input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder={t("subgroups.emailPlaceholder")}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
            />
            <button
              type="submit"
              disabled={sending || !inviteEmail.trim()}
              className="bg-pitch-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
            >
              {sending ? t("subgroups.sending") : t("subgroups.sendInvite")}
            </button>
          </form>
        </section>
      )}

      <section className="mb-8">
        <h2 className="text-lg font-semibold text-pitch-800 mb-3">{t("subgroups.rankingsTitle")}</h2>
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="overflow-x-auto overscroll-x-contain">
            <table className="w-full text-sm min-w-[36rem]">
              <thead>
                <tr className="bg-pitch-800 text-white">
                  <th className="text-left py-3 px-4 font-medium w-16">{t("rankings.rank")}</th>
                  <th className="text-left py-3 px-4 font-medium">{t("rankings.player")}</th>
                  <th className="py-3 px-4 font-medium text-center">{t("rankings.predictions")}</th>
                  <th className="py-3 px-4 font-medium text-center">{t("rankings.points")}</th>
                  {detail.my_role === "admin" && (
                    <th className="text-right py-3 px-4 font-medium w-28">
                      {t("subgroups.memberActions")}
                    </th>
                  )}
                </tr>
              </thead>
              <tbody>
                {rankingsItems(detail.rankings).map((r) => {
                  const memberMeta = detail.members.find((m) => m.user_id === r.user_id);
                  const canRemove =
                    detail.my_role === "admin" &&
                    memberMeta?.role === "member" &&
                    r.user_id !== user?.id;
                  return (
                    <tr
                      key={r.user_id}
                      className={`border-b last:border-0 ${
                        r.user_id === user?.id ? "bg-green-50 font-semibold" : "hover:bg-gray-50"
                      }`}
                    >
                      <td className="py-3 px-4 text-gray-700">{r.rank}</td>
                      <td className="py-3 px-4">
                        {r.username}
                        {r.user_id === user?.id && (
                          <span className="ml-1 text-xs text-pitch-600">{t("rankings.you")}</span>
                        )}
                        {memberMeta?.role === "admin" && (
                          <span className="ml-2 text-xs text-amber-800">({t("subgroups.roleAdmin")})</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">{r.predictions_made}</td>
                      <td className="py-3 px-4 text-center font-bold text-pitch-700">
                        {r.total_points}
                      </td>
                      {detail.my_role === "admin" && (
                        <td className="py-3 px-4 text-right">
                          {canRemove ? (
                            <button
                              type="button"
                              onClick={() => onRemoveMember(r.user_id, r.username)}
                              className="text-xs text-red-600 hover:text-red-800 font-medium"
                            >
                              {t("subgroups.removeMember")}
                            </button>
                          ) : (
                            <span className="text-gray-300">—</span>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {rankingsItems(detail.rankings).length === 0 && (
            <p className="text-gray-500 text-center py-6 text-sm">{t("subgroups.noMembers")}</p>
          )}
          <Pagination
            page={detail.rankings.page}
            totalPages={detail.rankings.total_pages}
            total={detail.rankings.total}
            onPageChange={setRankingsPage}
          />
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl border border-pitch-800/10 bg-white shadow-lg ring-1 ring-black/5">
        <div className="flex items-center justify-between gap-3 border-b border-pitch-800/10 bg-gradient-to-r from-pitch-800 to-pitch-700 px-4 py-3 sm:px-5">
          <div>
            <h2 className="text-base font-semibold text-white sm:text-lg">{t("subgroups.chatTitle")}</h2>
            <p className="text-xs text-pitch-50/80">{t("subgroups.chatMaxNote")}</p>
          </div>
          {messages.length > 0 && (
            <span className="shrink-0 rounded-full bg-white/15 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-sm">
              {messages.length}
            </span>
          )}
        </div>

        <div
          className="relative max-h-[min(28rem,55vh)] min-h-[16rem] overflow-y-auto scroll-smooth bg-gradient-to-b from-pitch-50/80 via-white to-gray-50/90 px-3 py-4 sm:px-5"
          aria-live="polite"
        >
          {messages.length === 0 ? (
            <div className="flex h-full min-h-[12rem] flex-col items-center justify-center px-4 text-center">
              <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-pitch-50 text-2xl shadow-inner ring-1 ring-pitch-600/10">
                💬
              </div>
              <p className="text-sm font-medium text-pitch-900">{t("subgroups.chatPlaceholder")}</p>
              <p className="mt-1 max-w-xs text-xs text-gray-500">{t("subgroups.chatMaxNote")}</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((m) => {
                const isOwn = m.user_id === user?.id;
                return (
                  <div
                    key={m.id}
                    className={`group flex gap-2.5 ${isOwn ? "flex-row-reverse" : "flex-row"}`}
                  >
                    {!isOwn && (
                      <div
                        className={`mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white shadow-sm ${avatarColorClass(m.username)}`}
                        aria-hidden
                      >
                        {avatarInitials(m.username)}
                      </div>
                    )}
                    <div
                      className={`relative max-w-[85%] sm:max-w-[75%] ${isOwn ? "items-end" : "items-start"} flex flex-col`}
                    >
                      <div
                        className={`flex items-baseline gap-2 ${isOwn ? "flex-row-reverse" : "flex-row"}`}
                      >
                        {!isOwn && (
                          <span className="text-xs font-semibold text-pitch-800">{m.username}</span>
                        )}
                        <time
                          className="text-[11px] text-gray-400 tabular-nums"
                          dateTime={m.created_at}
                        >
                          {formatChatTimestamp(m.created_at, locale)}
                        </time>
                      </div>
                      <div
                        className={`relative mt-1 rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed shadow-sm ${
                          isOwn
                            ? "rounded-tr-md bg-pitch-700 text-white"
                            : "rounded-tl-md border border-gray-100 bg-white text-gray-800"
                        }`}
                      >
                        <p className="whitespace-pre-wrap break-words">{m.body}</p>
                        {detail.my_role === "admin" && (
                          <button
                            type="button"
                            onClick={() => onDeleteMessage(m.id)}
                            className={`absolute -top-2 rounded-full border bg-white px-2 py-0.5 text-[10px] font-medium text-red-600 opacity-0 shadow-sm transition-opacity hover:bg-red-50 group-hover:opacity-100 ${
                              isOwn ? "-left-2" : "-right-2"
                            }`}
                          >
                            {t("subgroups.deleteMessage")}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          <div ref={chatEndRef} className="h-1" />
        </div>

        <form
          onSubmit={onSendMessage}
          className="border-t border-gray-100 bg-gray-50/80 p-3 sm:p-4"
        >
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
            <div className="relative flex-1">
              <textarea
                value={msgBody}
                onChange={(e) => setMsgBody(e.target.value)}
                placeholder={t("subgroups.chatPlaceholder")}
                rows={2}
                className="w-full min-h-[4.5rem] resize-none rounded-xl border border-gray-200 bg-white px-3.5 py-2.5 text-sm shadow-sm transition-shadow placeholder:text-gray-400 focus:border-pitch-600 focus:outline-none focus:ring-2 focus:ring-pitch-600/20"
                maxLength={2000}
              />
              <span className="pointer-events-none absolute bottom-2 right-2 text-[10px] tabular-nums text-gray-400">
                {msgBody.length}/2000
              </span>
            </div>
            <button
              type="submit"
              disabled={!msgBody.trim()}
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-pitch-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-pitch-800 disabled:cursor-not-allowed disabled:opacity-45 sm:min-h-[44px] touch-manipulation"
            >
              <span aria-hidden>➤</span>
              {t("subgroups.send")}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
