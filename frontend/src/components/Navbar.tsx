import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";
import LanguageSwitcher from "./LanguageSwitcher";
import { APP_VERSION } from "../version";
import api from "../api/client";
import type { SubgroupMine } from "../types";

const NAV_ITEMS = [
  { to: "/", labelKey: "navbar.dashboard" },
  { to: "/matches", labelKey: "navbar.matches" },
  { to: "/rankings", labelKey: "navbar.rankings" },
  { to: "/groups", labelKey: "navbar.groups" },
  { to: "/subgroups", labelKey: "navbar.subgroups" },
  { to: "/venues", labelKey: "navbar.venues" },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const { t } = useTranslation();
  const [helpOpen, setHelpOpen] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);
  const [pendingSubgroupInvites, setPendingSubgroupInvites] = useState(0);
  const [subgroupChatUnread, setSubgroupChatUnread] = useState(0);
  const helpWrapRef = useRef<HTMLDivElement>(null);
  const adminWrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!helpOpen) return;
    const onDown = (e: MouseEvent) => {
      if (helpWrapRef.current && !helpWrapRef.current.contains(e.target as Node)) {
        setHelpOpen(false);
      }
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [helpOpen]);

  useEffect(() => {
    if (!adminOpen) return;
    const onDown = (e: MouseEvent) => {
      if (adminWrapRef.current && !adminWrapRef.current.contains(e.target as Node)) {
        setAdminOpen(false);
      }
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [adminOpen]);

  useEffect(() => {
    setAdminOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!user) {
      setPendingSubgroupInvites(0);
      setSubgroupChatUnread(0);
      return;
    }
    const fetchSubgroupNav = () => {
      Promise.all([
        api.get<{ id: number }[]>("/subgroups/invites/pending"),
        api.get<SubgroupMine[]>("/subgroups/mine"),
      ])
        .then(([inv, mine]) => {
          setPendingSubgroupInvites(inv.data.length);
          setSubgroupChatUnread(
            mine.data.reduce((sum, s) => sum + (s.unread_message_count ?? 0), 0),
          );
        })
        .catch(() => {
          setPendingSubgroupInvites(0);
          setSubgroupChatUnread(0);
        });
    };
    fetchSubgroupNav();
    const onInvitesChanged = () => fetchSubgroupNav();
    const onMineChanged = () => fetchSubgroupNav();
    window.addEventListener("subgroups-invites-changed", onInvitesChanged);
    window.addEventListener("subgroups-mine-changed", onMineChanged);
    const interval = window.setInterval(fetchSubgroupNav, 60000);
    return () => {
      window.removeEventListener("subgroups-invites-changed", onInvitesChanged);
      window.removeEventListener("subgroups-mine-changed", onMineChanged);
      window.clearInterval(interval);
    };
  }, [user]);

  return (
    <>
      <nav className="bg-pitch-800 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2 font-bold text-xl">
              <span className="text-2xl">⚽</span>
              <span>{t("navbar.brand")}</span>
            </Link>

            {user && (
              <div className="flex items-center gap-1">
                {NAV_ITEMS.map((item) => (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors relative ${
                      item.to === "/subgroups"
                        ? location.pathname.startsWith("/subgroups")
                          ? "bg-pitch-900 text-white"
                          : "text-green-100 hover:bg-pitch-700"
                        : location.pathname === item.to
                          ? "bg-pitch-900 text-white"
                          : "text-green-100 hover:bg-pitch-700"
                    }`}
                  >
                    {t(item.labelKey)}
                    {item.to === "/subgroups" && pendingSubgroupInvites > 0 && (
                      <span className="absolute -top-0.5 -right-0.5 min-w-[1.1rem] h-[1.1rem] px-1 flex items-center justify-center rounded-full bg-amber-400 text-black text-[10px] font-bold">
                        {pendingSubgroupInvites > 9 ? "9+" : pendingSubgroupInvites}
                      </span>
                    )}
                    {item.to === "/subgroups" && subgroupChatUnread > 0 && (
                      <span
                        className={`absolute min-w-[1.1rem] h-[1.1rem] px-1 flex items-center justify-center rounded-full bg-sky-500 text-white text-[10px] font-bold ${
                          pendingSubgroupInvites > 0
                            ? "-top-0.5 -left-0.5"
                            : "-top-0.5 -right-0.5"
                        }`}
                      >
                        {subgroupChatUnread > 9 ? "9+" : subgroupChatUnread}
                      </span>
                    )}
                  </Link>
                ))}
                {user.is_admin && (
                  <div className="relative" ref={adminWrapRef}>
                    <button
                      type="button"
                      onClick={() => setAdminOpen((o) => !o)}
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1 ${
                        location.pathname.startsWith("/admin")
                          ? "bg-amber-500 text-black"
                          : "text-amber-200 hover:bg-pitch-700"
                      }`}
                      aria-expanded={adminOpen}
                      aria-haspopup="true"
                    >
                      {t("navbar.admin")}
                      <span className="text-xs opacity-80" aria-hidden>
                        ▾
                      </span>
                    </button>
                    {adminOpen && (
                      <div
                        className="absolute left-0 mt-1 py-1 min-w-[12rem] bg-white text-gray-900 rounded-md shadow-lg z-50 border border-gray-100"
                        role="menu"
                      >
                        <NavLink
                          to="/admin/scores"
                          role="menuitem"
                          onClick={() => setAdminOpen(false)}
                          className={({ isActive }) =>
                            `block px-4 py-2 text-sm hover:bg-gray-100 ${
                              isActive ? "bg-amber-50 font-medium text-amber-900" : ""
                            }`
                          }
                        >
                          {t("navbar.adminSubmenuScores")}
                        </NavLink>
                        <NavLink
                          to="/admin/settings"
                          role="menuitem"
                          onClick={() => setAdminOpen(false)}
                          className={({ isActive }) =>
                            `block px-4 py-2 text-sm hover:bg-gray-100 ${
                              isActive ? "bg-amber-50 font-medium text-amber-900" : ""
                            }`
                          }
                        >
                          {t("navbar.adminSubmenuSettings")}
                        </NavLink>
                        <NavLink
                          to="/admin/subgroups"
                          role="menuitem"
                          onClick={() => setAdminOpen(false)}
                          className={({ isActive }) =>
                            `block px-4 py-2 text-sm hover:bg-gray-100 ${
                              isActive ? "bg-amber-50 font-medium text-amber-900" : ""
                            }`
                          }
                        >
                          {t("navbar.adminSubmenuSubgroups")}
                        </NavLink>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="flex items-center gap-3">
              <div className="relative" ref={helpWrapRef}>
                <button
                  type="button"
                  onClick={() => setHelpOpen((o) => !o)}
                  className="px-3 py-2 rounded-md text-sm font-medium text-green-100 hover:bg-pitch-700 transition-colors"
                  aria-expanded={helpOpen}
                  aria-haspopup="true"
                >
                  {t("navbar.help")}
                </button>
                {helpOpen && (
                  <div
                    className="absolute right-0 mt-1 py-1 min-w-[10rem] bg-white text-gray-900 rounded-md shadow-lg z-50 border border-gray-100"
                    role="menu"
                  >
                    <button
                      type="button"
                      role="menuitem"
                      className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100"
                      onClick={() => {
                        setAboutOpen(true);
                        setHelpOpen(false);
                      }}
                    >
                      {t("navbar.about")}
                    </button>
                  </div>
                )}
              </div>
              <LanguageSwitcher />
              {user && (
                <>
                  <span className="text-sm text-green-200">
                    {user.username}
                    {user.is_admin && (
                      <span className="ml-1 text-xs bg-yellow-500 text-black px-1.5 py-0.5 rounded-full">
                        {t("navbar.admin")}
                      </span>
                    )}
                  </span>
                  <button
                    onClick={logout}
                    className="text-sm bg-pitch-900 hover:bg-red-700 px-3 py-1.5 rounded-md transition-colors"
                  >
                    {t("navbar.logout")}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {aboutOpen && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
          role="presentation"
          onClick={() => setAboutOpen(false)}
        >
          <div
            className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 text-gray-900"
            role="dialog"
            aria-labelledby="about-title"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="about-title" className="text-lg font-bold text-pitch-800 mb-3">
              {t("helpAbout.title")}
            </h2>
            <p className="text-sm text-gray-600 mb-6 font-mono">
              {t("helpAbout.versionLine", { version: APP_VERSION })}
            </p>
            <button
              type="button"
              onClick={() => setAboutOpen(false)}
              className="text-sm bg-pitch-700 hover:bg-pitch-800 text-white px-4 py-2 rounded-md transition-colors"
            >
              {t("helpAbout.close")}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
