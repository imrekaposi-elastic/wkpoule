import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "../api/client";
import { beforeAuthenticatedPoll } from "../api/authenticatedPoll";
import { useAuth } from "../context/AuthContext";
import type {
  SubgroupDirectory,
  SubgroupInvitePending,
  SubgroupJoinRequestRow,
  SubgroupMine,
} from "../types";

export default function Subgroups() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [mine, setMine] = useState<SubgroupMine[]>([]);
  const [directory, setDirectory] = useState<SubgroupDirectory[]>([]);
  const [pending, setPending] = useState<SubgroupInvitePending[]>([]);
  const [incoming, setIncoming] = useState<SubgroupJoinRequestRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [applyingId, setApplyingId] = useState<number | null>(null);
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const [banner, setBanner] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    Promise.all([
      api.get<SubgroupMine[]>("/subgroups/mine"),
      api.get<SubgroupDirectory[]>("/subgroups/directory"),
      api.get<SubgroupInvitePending[]>("/subgroups/invites/pending"),
      api.get<SubgroupJoinRequestRow[]>("/subgroups/join-requests/incoming"),
    ])
      .then(([m, d, p, inc]) => {
        setMine(m.data);
        setDirectory(d.data);
        setPending(p.data);
        setIncoming(inc.data);
      })
      .catch(() => {
        setMine([]);
        setDirectory([]);
        setPending([]);
        setIncoming([]);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!user) return;
    const refreshMine = () => {
      void beforeAuthenticatedPoll().then((ok) => {
        if (!ok) return;
        api
          .get<SubgroupMine[]>("/subgroups/mine")
          .then((r) => setMine(r.data))
          .catch(() => {});
      });
    };
    const tmr = window.setInterval(refreshMine, 30000);
    const onMineChanged = () => {
      load();
    };
    window.addEventListener("subgroups-mine-changed", onMineChanged);
    return () => {
      window.clearInterval(tmr);
      window.removeEventListener("subgroups-mine-changed", onMineChanged);
    };
  }, [load, user]);

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
      window.dispatchEvent(new Event("subgroups-mine-changed"));
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
      window.dispatchEvent(new Event("subgroups-mine-changed"));
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

  const onApply = async (subgroupId: number) => {
    setApplyingId(subgroupId);
    setBanner(null);
    try {
      await api.post(`/subgroups/${subgroupId}/join-requests`);
      setBanner({ ok: true, text: t("subgroups.applicationSent") });
      load();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail;
      setBanner({
        ok: false,
        text: typeof detail === "string" ? detail : t("subgroups.applicationFailed"),
      });
    } finally {
      setApplyingId(null);
    }
  };

  const onCancelApplication = async (subgroupId: number) => {
    setApplyingId(subgroupId);
    try {
      await api.delete(`/subgroups/${subgroupId}/join-requests/mine`);
      setBanner({ ok: true, text: t("subgroups.applicationCancelled") });
      load();
    } catch {
      setBanner({ ok: false, text: t("subgroups.applicationCancelFailed") });
    } finally {
      setApplyingId(null);
    }
  };

  const onApproveApplication = async (req: SubgroupJoinRequestRow) => {
    setReviewingId(req.id);
    setBanner(null);
    try {
      await api.post(`/subgroups/${req.subgroup_id}/join-requests/${req.id}/approve`);
      setBanner({
        ok: true,
        text: t("subgroups.applicationApproved", { username: req.username }),
      });
      load();
      window.dispatchEvent(new Event("subgroups-mine-changed"));
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail;
      setBanner({
        ok: false,
        text: typeof detail === "string" ? detail : t("subgroups.applicationReviewFailed"),
      });
    } finally {
      setReviewingId(null);
    }
  };

  const onRejectApplication = async (req: SubgroupJoinRequestRow) => {
    setReviewingId(req.id);
    try {
      await api.post(`/subgroups/${req.subgroup_id}/join-requests/${req.id}/reject`);
      setBanner({
        ok: true,
        text: t("subgroups.applicationRejected", { username: req.username }),
      });
      load();
    } catch {
      setBanner({ ok: false, text: t("subgroups.applicationReviewFailed") });
    } finally {
      setReviewingId(null);
    }
  };

  const browseRows = directory.filter(
    (sg) => sg.membership_status === "none" || sg.membership_status === "application_pending",
  );

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

      {incoming.length > 0 && (
        <section className="mb-10">
          <h2 className="text-lg font-semibold text-pitch-800 mb-3">
            {t("subgroups.incomingApplications")}
          </h2>
          <ul className="space-y-3">
            {incoming.map((req) => (
              <li
                key={req.id}
                className="bg-sky-50 border border-sky-200 rounded-lg p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
              >
                <div>
                  <p className="font-medium text-sky-950">
                    {req.username}{" "}
                    <span className="font-normal text-sky-900/80">
                      → {req.subgroup_name}
                    </span>
                  </p>
                  <p className="text-xs text-sky-900/70">{t("subgroups.applicationWantsToJoin")}</p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    type="button"
                    disabled={reviewingId === req.id}
                    onClick={() => onApproveApplication(req)}
                    className="text-sm bg-pitch-700 text-white px-3 py-1.5 rounded-md hover:bg-pitch-800 disabled:opacity-50"
                  >
                    {t("subgroups.approveApplication")}
                  </button>
                  <button
                    type="button"
                    disabled={reviewingId === req.id}
                    onClick={() => onRejectApplication(req)}
                    className="text-sm border border-gray-300 px-3 py-1.5 rounded-md hover:bg-white disabled:opacity-50"
                  >
                    {t("subgroups.rejectApplication")}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

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

      <section className="mb-10">
        <h2 className="text-lg font-semibold text-pitch-800 mb-3">{t("subgroups.browseSubgroups")}</h2>
        {browseRows.length === 0 ? (
          <p className="text-gray-500 text-sm">{t("subgroups.browseEmpty")}</p>
        ) : (
          <ul className="space-y-2">
            {browseRows.map((sg) => (
              <li
                key={sg.id}
                className="flex items-center justify-between gap-3 bg-white rounded-lg border border-gray-100 shadow-sm px-4 py-3"
              >
                <div>
                  <span className="font-medium text-pitch-900">{sg.name}</span>
                  <span className="text-sm text-gray-500 ml-2">
                    ({t("subgroups.memberCount", { count: sg.member_count })})
                  </span>
                </div>
                {sg.membership_status === "application_pending" ? (
                  <button
                    type="button"
                    disabled={applyingId === sg.id}
                    onClick={() => onCancelApplication(sg.id)}
                    className="text-sm border border-gray-300 px-3 py-1.5 rounded-md hover:bg-gray-50 disabled:opacity-50 shrink-0"
                  >
                    {applyingId === sg.id
                      ? t("subgroups.applying")
                      : t("subgroups.cancelApplication")}
                  </button>
                ) : (
                  <button
                    type="button"
                    disabled={applyingId === sg.id}
                    onClick={() => onApply(sg.id)}
                    className="text-sm bg-pitch-700 text-white px-3 py-1.5 rounded-md hover:bg-pitch-800 disabled:opacity-50 shrink-0"
                  >
                    {applyingId === sg.id
                      ? t("subgroups.applying")
                      : t("subgroups.applyToJoin")}
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

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
