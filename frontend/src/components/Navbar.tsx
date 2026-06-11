import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";
import LanguageSwitcher from "./LanguageSwitcher";
import { APP_VERSION } from "../version";
import api from "../api/client";
import { beforeAuthenticatedPoll } from "../api/authenticatedPoll";
import type { SubgroupMine } from "../types";

const NAV_ITEMS = [
  { to: "/", labelKey: "navbar.dashboard" },
  { to: "/matches", labelKey: "navbar.matches" },
  { to: "/rankings", labelKey: "navbar.rankings" },
  { to: "/groups", labelKey: "navbar.groups" },
  { to: "/teams", labelKey: "navbar.teams" },
  { to: "/subgroups", labelKey: "navbar.subgroups" },
  { to: "/venues", labelKey: "navbar.venues" },
] as const;

function navItemActive(pathname: string, to: string): boolean {
  if (to === "/subgroups") return pathname.startsWith("/subgroups");
  if (to === "/teams") return pathname.startsWith("/teams");
  return pathname === to;
}

function IconMenu(props: { className?: string }) {
  return (
    <svg className={props.className} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function IconClose(props: { className?: string }) {
  return (
    <svg className={props.className} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const { t } = useTranslation();
  const [helpOpen, setHelpOpen] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
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
    setMobileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!mobileOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [mobileOpen]);

  useEffect(() => {
    if (!user) {
      setPendingSubgroupInvites(0);
      setSubgroupChatUnread(0);
      return;
    }
    const fetchSubgroupNav = () => {
      void beforeAuthenticatedPoll().then((ok) => {
        if (!ok) return;
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

  const desktopLinkClass = (to: string) => {
    const base =
      to === "/subgroups"
        ? location.pathname.startsWith("/subgroups")
        : to === "/teams"
          ? location.pathname.startsWith("/teams")
          : location.pathname === to;
    return `px-3 py-2 rounded-md text-sm font-medium transition-colors relative ${
      base ? "bg-pitch-900 text-white" : "text-green-100 hover:bg-pitch-700"
    }`;
  };

  return (
    <>
      <nav className="bg-pitch-800 text-white shadow-lg sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
          <div className="flex items-center justify-between gap-2 h-14 sm:h-16">
            <Link
              to="/"
              className="flex items-center gap-2 font-bold text-lg sm:text-xl shrink-0 min-w-0"
              onClick={() => setMobileOpen(false)}
            >
              <span className="text-2xl shrink-0" aria-hidden>
                ⚽
              </span>
              <span className="truncate">{t("navbar.brand")}</span>
            </Link>

            {user && (
              <div className="hidden lg:flex items-center justify-center flex-1 min-w-0 px-2">
                <div className="flex items-center gap-0.5 justify-center">
                  {NAV_ITEMS.map((item) => (
                    <Link
                      key={item.to}
                      to={item.to}
                      className={desktopLinkClass(item.to)}
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
                            pendingSubgroupInvites > 0 ? "-top-0.5 -left-0.5" : "-top-0.5 -right-0.5"
                          }`}
                        >
                          {subgroupChatUnread > 9 ? "9+" : subgroupChatUnread}
                        </span>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center gap-1 sm:gap-2 shrink-0">
              <div className="relative" ref={helpWrapRef}>
                <button
                  type="button"
                  onClick={() => setHelpOpen((o) => !o)}
                  className="px-2 sm:px-3 py-2 rounded-md text-sm font-medium text-green-100 hover:bg-pitch-700 transition-colors"
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
                  {user.is_admin && (
                    <div className="relative hidden lg:block" ref={adminWrapRef}>
                      <button
                        type="button"
                        onClick={() => setAdminOpen((o) => !o)}
                        className={`px-2.5 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1 ${
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
                          className="absolute right-0 mt-1 py-1 min-w-[12rem] bg-white text-gray-900 rounded-md shadow-lg z-50 border border-gray-100"
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
                  <div className="hidden lg:flex flex-col items-end ml-1 pl-2 border-l border-pitch-700/80 min-w-0">
                    <div className="flex items-center gap-1.5 max-w-[9rem]">
                      <Link
                        to="/profile"
                        className="text-sm text-green-100 truncate font-medium hover:text-white transition-colors"
                        title={t("navbar.profile")}
                      >
                        {user.username}
                      </Link>
                      {user.is_admin && (
                        <span className="text-[10px] bg-yellow-500 text-black px-1.5 py-0.5 rounded-full whitespace-nowrap shrink-0 font-semibold">
                          {t("navbar.admin")}
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={logout}
                      className="text-xs text-green-300/90 hover:text-white transition-colors mt-0.5"
                    >
                      {t("navbar.logout")}
                    </button>
                  </div>
                  <button
                    type="button"
                    className="lg:hidden inline-flex items-center justify-center rounded-md p-2 text-green-100 hover:bg-pitch-700 touch-manipulation"
                    aria-expanded={mobileOpen}
                    aria-controls="mobile-nav-menu"
                    onClick={() => setMobileOpen((o) => !o)}
                  >
                    <span className="sr-only">
                      {mobileOpen ? t("navbar.closeMenu") : t("navbar.openMenu")}
                    </span>
                    {mobileOpen ? <IconClose className="w-6 h-6" /> : <IconMenu className="w-6 h-6" />}
                  </button>
                </>
              )}
            </div>
          </div>

          {user && mobileOpen && (
            <div
              id="mobile-nav-menu"
              className="lg:hidden border-t border-pitch-900/60 bg-pitch-900 max-h-[min(75vh,calc(100dvh-3.5rem))] overflow-y-auto overscroll-y-contain pb-[max(1rem,env(safe-area-inset-bottom))]"
            >
              <div className="py-2 px-1 space-y-0.5">
                {NAV_ITEMS.map((item) => {
                  const active = navItemActive(location.pathname, item.to);
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      onClick={() => setMobileOpen(false)}
                      className={`flex items-center justify-between gap-2 rounded-md px-3 py-3 text-sm font-medium touch-manipulation min-h-[44px] ${
                        active ? "bg-pitch-800 text-white" : "text-green-100 hover:bg-pitch-800/80"
                      }`}
                    >
                      <span>{t(item.labelKey)}</span>
                      {item.to === "/subgroups" && (pendingSubgroupInvites > 0 || subgroupChatUnread > 0) && (
                        <span className="flex items-center gap-1 shrink-0">
                          {pendingSubgroupInvites > 0 && (
                            <span className="min-w-[1.25rem] h-6 px-1.5 flex items-center justify-center rounded-full bg-amber-400 text-black text-xs font-bold">
                              {pendingSubgroupInvites > 99 ? "99+" : pendingSubgroupInvites}
                            </span>
                          )}
                          {subgroupChatUnread > 0 && (
                            <span className="min-w-[1.25rem] h-6 px-1.5 flex items-center justify-center rounded-full bg-sky-500 text-white text-xs font-bold">
                              {subgroupChatUnread > 99 ? "99+" : subgroupChatUnread}
                            </span>
                          )}
                        </span>
                      )}
                    </Link>
                  );
                })}
                {user.is_admin && (
                  <div className="pt-2 mt-2 border-t border-pitch-800">
                    <p className="px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-200/90">
                      {t("navbar.admin")}
                    </p>
                    <Link
                      to="/admin/scores"
                      onClick={() => setMobileOpen(false)}
                      className={`block rounded-md px-3 py-3 text-sm font-medium touch-manipulation ${
                        location.pathname.startsWith("/admin/scores")
                          ? "bg-amber-500 text-black"
                          : "text-amber-100 hover:bg-pitch-800"
                      }`}
                    >
                      {t("navbar.adminSubmenuScores")}
                    </Link>
                    <Link
                      to="/admin/settings"
                      onClick={() => setMobileOpen(false)}
                      className={`block rounded-md px-3 py-3 text-sm font-medium touch-manipulation ${
                        location.pathname.startsWith("/admin/settings")
                          ? "bg-amber-500 text-black"
                          : "text-amber-100 hover:bg-pitch-800"
                      }`}
                    >
                      {t("navbar.adminSubmenuSettings")}
                    </Link>
                    <Link
                      to="/admin/subgroups"
                      onClick={() => setMobileOpen(false)}
                      className={`block rounded-md px-3 py-3 text-sm font-medium touch-manipulation ${
                        location.pathname.startsWith("/admin/subgroups")
                          ? "bg-amber-500 text-black"
                          : "text-amber-100 hover:bg-pitch-800"
                      }`}
                    >
                      {t("navbar.adminSubmenuSubgroups")}
                    </Link>
                  </div>
                )}
                <div className="pt-3 mt-2 border-t border-pitch-800 px-3 pb-3 space-y-3">
                  <button
                    type="button"
                    className="w-full text-left text-sm text-green-100 hover:text-white py-1"
                    onClick={() => {
                      setAboutOpen(true);
                      setMobileOpen(false);
                    }}
                  >
                    {t("navbar.about")}
                  </button>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2 text-sm text-green-200">
                      <Link
                        to="/profile"
                        onClick={() => setMobileOpen(false)}
                        className="font-medium hover:text-white"
                      >
                        {user.username}
                      </Link>
                      {user.is_admin && (
                        <span className="text-xs bg-yellow-500 text-black px-1.5 py-0.5 rounded-full">
                          {t("navbar.admin")}
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setMobileOpen(false);
                        logout();
                      }}
                      className="text-left text-sm text-green-300 hover:text-white py-1 touch-manipulation"
                    >
                      {t("navbar.logout")}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </nav>

      {aboutOpen && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
          role="presentation"
          onClick={() => setAboutOpen(false)}
        >
          <div
            className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 text-gray-900 max-h-[90dvh] overflow-y-auto"
            role="dialog"
            aria-labelledby="about-title"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="about-title" className="text-lg font-bold text-pitch-800 mb-3">
              {t("helpAbout.title")}
            </h2>
            <p className="text-sm text-gray-600 mb-6 font-mono break-all">
              {t("helpAbout.versionLine", { version: APP_VERSION })}
            </p>
            <button
              type="button"
              onClick={() => setAboutOpen(false)}
              className="text-sm bg-pitch-700 hover:bg-pitch-800 text-white px-4 py-2 rounded-md transition-colors touch-manipulation min-h-[44px] w-full sm:w-auto"
            >
              {t("helpAbout.close")}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
