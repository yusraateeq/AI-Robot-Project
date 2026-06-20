"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { cn } from "../lib/cn";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" },
  { href: "/dashboard/bots", label: "AI bots", icon: "M12 2a3 3 0 0 1 3 3v1h1a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3h1V5a3 3 0 0 1 3-3zm-3 9a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm6 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z" },
  { href: "/logs", label: "Call logs", icon: "M6 2h9l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm8 1.5V8h4.5" },
  { href: "/settings", label: "Settings", icon: "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm8.4 3a8.4 8.4 0 0 0-.15-1.55l2.1-1.65-2-3.46-2.45 1a8.5 8.5 0 0 0-2.7-1.55l-.4-2.6h-4l-.4 2.6a8.5 8.5 0 0 0-2.7 1.55l-2.45-1-2 3.46 2.1 1.65A8.4 8.4 0 0 0 3.6 12c0 .53.05 1.05.15 1.55l-2.1 1.65 2 3.46 2.45-1c.8.65 1.7 1.18 2.7 1.55l.4 2.6h4l.4-2.6a8.5 8.5 0 0 0 2.7-1.55l2.45 1 2-3.46-2.1-1.65c.1-.5.15-1.02.15-1.55z" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="fixed left-4 top-4 z-30 inline-flex items-center justify-center rounded-md border border-border-soft bg-panel p-2 text-text-secondary shadow-sm md:hidden"
        aria-label="Open navigation"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 6h18M3 12h18M3 18h18" strokeLinecap="round" />
        </svg>
      </button>

      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-60 shrink-0 border-r border-border-soft bg-panel transition-transform md:static md:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-14 items-center gap-2.5 border-b border-border-soft px-5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-signal/15 text-xs font-semibold text-signal">
            R
          </div>
          <span className="text-sm font-semibold tracking-tight text-text-primary">
            Redstone
          </span>
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
                onClick={() => setIsOpen(false)}
                className={cn(
                  "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-signal/10 text-signal"
                    : "text-text-secondary hover:bg-panel-raised hover:text-text-primary"
                )}
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
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="absolute bottom-0 left-0 w-full border-t border-border-soft p-3">
          <div className="flex items-center gap-2.5 rounded-md bg-panel-raised px-3 py-2.5">
            <span className="signal-dot h-2 w-2 rounded-full bg-signal" />
            <div>
              <p className="text-xs font-medium text-text-primary">System nominal</p>
              <p className="font-mono text-[11px] text-text-tertiary">VICIdial · campaign 4</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}