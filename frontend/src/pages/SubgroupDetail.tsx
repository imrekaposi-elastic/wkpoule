import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import { resolveLocale } from "../i18n/languages";
import type { SubgroupDetail as SubgroupDetailType, SubgroupMessage } from "../types";

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

  const loadDetail = useCallback(() => {
    if (Number.isNaN(subgroupId)) return;
    api
      .get<SubgroupDetailType>(`/subgroups/${subgroupId}`)
      .then((r) => setDetail(r.data))
      .catch(() => setDetail(null));
  }, [subgroupId]);

  useEffect(() => {
    if (Number.isNaN(subgroupId)) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      api.get<SubgroupDetailType>(`/subgroups/${subgroupId}`),
      api.get<SubgroupMessage[]>(`/subgroups/${subgroupId}/messages`),
    ])
      .then(([d, m]) => {
        setDetail(d.data);
        setMessages(m.data);
        window.dispatchEvent(new Event("subgroups-mine-changed"));
      })
      .catch(() => {
        setDetail(null);
        setMessages([]);
      })
      .finally(() => setLoading(false));
  }, [subgroupId]);

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
      loadDetail();
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
                {detail.rankings.map((r) => {
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
          {detail.rankings.length === 0 && (
            <p className="text-gray-500 text-center py-6 text-sm">{t("subgroups.noMembers")}</p>
          )}
        </div>
      </section>

      <section className="bg-white rounded-xl shadow-md border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-pitch-800 mb-1">{t("subgroups.chatTitle")}</h2>
        <p className="text-xs text-gray-500 mb-3">{t("subgroups.chatMaxNote")}</p>
        <div className="border border-gray-200 rounded-lg h-64 overflow-y-auto p-3 bg-gray-50 mb-3 text-sm space-y-2">
          {messages.map((m) => (
            <div key={m.id} className="text-gray-800 group">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <span className="font-medium text-pitch-800">{m.username}</span>
                  <span className="text-xs text-gray-400 ml-2">
                    {new Date(m.created_at).toLocaleString(locale, {
                      dateStyle: "short",
                      timeStyle: "short",
                    })}
                  </span>
                  <p className="mt-0.5 whitespace-pre-wrap break-words">{m.body}</p>
                </div>
                {detail.my_role === "admin" && (
                  <button
                    type="button"
                    onClick={() => onDeleteMessage(m.id)}
                    className="shrink-0 text-xs text-red-600 hover:text-red-800 px-1"
                  >
                    {t("subgroups.deleteMessage")}
                  </button>
                )}
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
        <form onSubmit={onSendMessage} className="flex flex-col sm:flex-row gap-2">
          <textarea
            value={msgBody}
            onChange={(e) => setMsgBody(e.target.value)}
            placeholder={t("subgroups.chatPlaceholder")}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm min-h-[4rem] w-full min-w-0"
            maxLength={2000}
          />
          <button
            type="submit"
            disabled={!msgBody.trim()}
            className="sm:self-end shrink-0 bg-pitch-700 text-white px-4 py-2.5 rounded-lg text-sm font-medium disabled:opacity-50 touch-manipulation min-h-[44px]"
          >
            {t("subgroups.send")}
          </button>
        </form>
      </section>
    </div>
  );
}
