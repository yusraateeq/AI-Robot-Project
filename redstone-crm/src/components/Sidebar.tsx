"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { signOut } from "firebase/auth";
import { auth } from "@/src/lib/firebase";
import { cn } from "../lib/cn";
import { getToken, removeToken, fetchProfile, type Profile } from "@/src/lib/api";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" },
  { href: "/dashboard/bots", label: "AI bots", icon: "M12 2a3 3 0 0 1 3 3v1h1a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3h1V5a3 3 0 0 1 3-3zm-3 9a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm6 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z" },
  { href: "/logs", label: "Call logs", icon: "M6 2h9l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm8 1.5V8h4.5" },
  { href: "/settings", label: "Settings", icon: "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm8.4 3a8.4 8.4 0 0 0-.15-1.55l2.1-1.65-2-3.46-2.45 1a8.5 8.5 0 0 0-2.7-1.55l-.4-2.6h-4l-.4 2.6a8.5 8.5 0 0 0-2.7 1.55l-2.45-1-2 3.46 2.1 1.65A8.4 8.4 0 0 0 3.6 12c0 .53.05 1.05.15 1.55l-2.1 1.65 2 3.46 2.45-1c.8.65 1.7 1.18 2.7 1.55l.4 2.6h4l.4-2.6a8.5 8.5 0 0 0 2.7-1.55l2.45 1 2-3.46-2.1-1.65c.1-.5.15-1.02.15-1.55z" },
  { href: "/dashboard/profile", label: "Profile", icon: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm-8 8c0-4 3.6-6 8-6s8 2 8 6" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("sidebar_collapsed") === "true";
    }
    return false;
  });
  const [profile, setProfile] = useState<Profile | null>(null);

  useEffect(() => {
    if (getToken()) {
      fetchProfile().then(setProfile).catch(() => {});
    }
  }, []);

  function toggleCollapsed() {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("sidebar_collapsed", String(next));
      return next;
    });
  }

  async function handleLogout() {
    removeToken();
    await signOut(auth);
    router.replace("/login");
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setMobileOpen(true)}
        className="fixed left-4 top-4 z-30 inline-flex items-center justify-center rounded-md border border-border-soft bg-panel p-2 text-text-secondary shadow-sm md:hidden"
        aria-label="Open navigation"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 6h18M3 12h18M3 18h18" strokeLinecap="round" />
        </svg>
      </button>

      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex flex-col border-r border-border-soft bg-panel transition-all duration-200",
          collapsed ? "w-16" : "w-60",
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        <div className={cn(
          "flex h-14 items-center border-b border-border-soft",
          collapsed ? "justify-center px-0" : "justify-between px-4"
        )}>
          {!collapsed && (
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-signal/15 text-xs font-semibold text-signal">
                R
              </div>
              <span className="text-sm font-semibold tracking-tight text-text-primary">
                Redstone
              </span>
            </div>
          )}
          <button
            type="button"
            onClick={toggleCollapsed}
            className={cn(
              "flex items-center justify-center rounded-md text-text-tertiary transition-colors hover:bg-panel-raised hover:text-text-primary",
              collapsed ? "h-8 w-8" : "h-7 w-7"
            )}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className={cn("transition-transform", collapsed ? "rotate-180" : "")}
            >
              <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>

        <nav className="flex flex-col gap-1 p-3">
          {NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "group flex items-center gap-3 rounded-md transition-colors",
                  collapsed ? "justify-center px-2 py-2.5" : "px-3 py-2",
                  isActive
                    ? "bg-signal/10 text-signal"
                    : "text-text-secondary hover:bg-panel-raised hover:text-text-primary"
                )}
                title={collapsed ? item.label : undefined}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  className={cn(
                    "shrink-0 transition-colors",
                    isActive ? "text-signal" : "text-text-tertiary group-hover:text-text-secondary"
                  )}
                >
                  <path d={item.icon} strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {!collapsed && (
                  <span className="text-sm font-medium">{item.label}</span>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto border-t border-border-soft p-3">
          <button
            type="button"
            onClick={handleLogout}
            className={cn(
              "flex w-full items-center gap-2.5 rounded-md transition-colors hover:bg-red-dim/10",
              collapsed ? "justify-center px-1 py-2" : "px-3 py-2.5"
            )}
            title={collapsed ? "Logout" : undefined}
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-panel-raised text-xs font-medium text-text-secondary">
              {profile?.avatar_url || profile?.email?.[0]?.toUpperCase() || "?"}
            </div>
            {!collapsed && (
              <div className="flex-1 min-w-0 text-left">
                <p className="truncate text-xs font-medium text-text-primary">
                  {profile?.display_name || profile?.username || "User"}
                </p>
                <p className="truncate font-mono text-[11px] text-text-tertiary">
                  {profile?.email || "No email"}
                </p>
              </div>
            )}
            {!collapsed && (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0 text-text-tertiary">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
