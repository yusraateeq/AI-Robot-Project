"use client";

import { useState, useEffect } from "react";
import { Bot, BotStatus } from "../lib/types";
import { cn } from "../lib/cn";

interface BotCardProps {
  bot: Bot;
  onLogin?: (botId: string) => void;
  onLogout?: (botId: string) => void;
  onRestart?: (botId: string) => void;
  onEdit?: (botId: string) => void;
  onDelete?: (botId: string) => void;
}

const STATUS_CONFIG: Record<
  BotStatus,
  { label: string; dot: string; text: string; ring: string; pulse: boolean }
> = {
  active: {
    label: "Active",
    dot: "bg-signal",
    text: "text-signal",
    ring: "border-signal/30 bg-signal/10",
    pulse: true,
  },
  online: {
    label: "Online",
    dot: "bg-sky-400",
    text: "text-sky-400",
    ring: "border-sky-400/30 bg-sky-400/10",
    pulse: true,
  },
  offline: {
    label: "Offline",
    dot: "bg-text-tertiary",
    text: "text-text-tertiary",
    ring: "border-border-soft bg-panel-raised",
    pulse: false,
  },
  restarting: {
    label: "Restarting",
    dot: "bg-amber",
    text: "text-amber",
    ring: "border-amber/30 bg-amber/10",
    pulse: false,
  },
};

export default function BotCard({
  bot,
  onLogin,
  onLogout,
  onRestart,
  onEdit,
  onDelete,
}: BotCardProps) {
  const [pendingAction, setPendingAction] = useState<
    "login" | "logout" | "restart" | null
  >(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [localStatus, setLocalStatus] = useState<BotStatus | null>(null);

  const effectiveStatus = localStatus ?? bot.status;

  useEffect(() => {
    if (effectiveStatus !== "online") return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/bots/${bot.id}/status`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.vicidial_status && data.vicidial_status.toUpperCase().includes("READY")) {
          setLocalStatus("active");
        }
      } catch {
        // network errors ignored during polling
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [effectiveStatus, bot.id]);
  const status = STATUS_CONFIG[effectiveStatus];
  const isOffline = effectiveStatus === "offline";
  const isRestarting = effectiveStatus === "restarting";

  async function handleLoginClick() {
    if (pendingAction) return;
    setPendingAction("login");
    setLoginError(null);
    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bot_id: bot.id }),
      });
      if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
          const body = await res.json();
          detail = body.detail || body.error || detail;
        } catch {
          const text = await res.text().catch(() => "");
          if (text) detail = text;
        }
        throw new Error(detail);
      }
      setLocalStatus("online");
      if (onLogin) {
        await onLogin(bot.id);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setLoginError(msg);
    } finally {
      setPendingAction(null);
    }
  }

  async function handleAction(
    action: "login" | "logout" | "restart",
    handler?: (botId: string) => void
  ) {
    if (!handler || pendingAction) return;
    setLocalStatus(null);
    setPendingAction(action);
    try {
      await handler(bot.id);
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <div className="group rounded-lg border border-border-soft bg-panel p-5 transition-all duration-200 hover:-translate-y-0.5 hover:border-border-strong hover:shadow-[0_8px_24px_-8px_rgba(0,0,0,0.5)]">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-mono text-sm font-medium text-text-primary">
            {bot.name}
          </h3>
          <p className="mt-0.5 text-xs text-text-secondary">{bot.campaign}</p>
        </div>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
            status.ring,
            status.text
          )}
        >
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              status.dot,
              status.pulse && "signal-dot"
            )}
          />
          {status.label}
        </span>
      </div>

      <div className="mt-4 flex items-baseline gap-1.5">
        <span className="font-mono text-2xl font-medium text-text-primary">
          {bot.callsToday}
        </span>
        <span className="text-xs text-text-tertiary">calls today</span>
      </div>

      <div className="mt-5 flex gap-2">
        <button
          type="button"
          onClick={handleLoginClick}
          disabled={!isOffline || pendingAction !== null}
          className="flex-1 rounded-md bg-signal/15 px-3 py-2 text-xs font-medium text-signal transition-colors hover:bg-signal/25 disabled:cursor-not-allowed disabled:bg-panel-raised disabled:text-text-tertiary"
        >
          {pendingAction === "login" ? "Logging in\u2026" : "Login"}
        </button>
        <button
          type="button"
          onClick={() => handleAction("logout", onLogout)}
          disabled={isOffline || pendingAction !== null}
          className="flex-1 rounded-md border border-border-soft px-3 py-2 text-xs font-medium text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary disabled:cursor-not-allowed disabled:text-text-tertiary"
        >
          {pendingAction === "logout" ? "Logging out\u2026" : "Logout"}
        </button>
        <button
          type="button"
          onClick={() => handleAction("restart", onRestart)}
          disabled={isOffline || isRestarting || pendingAction !== null}
          className="flex-1 rounded-md border border-border-soft px-3 py-2 text-xs font-medium text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary disabled:cursor-not-allowed disabled:text-text-tertiary"
        >
          {pendingAction === "restart" ? "Restarting\u2026" : "Restart"}
        </button>
      </div>

      {loginError && (
        <div className="mt-3 rounded-md border border-red/30 bg-red-dim/10 px-3 py-2 text-xs text-red">
          <span className="font-medium">Login failed:</span> {loginError}
        </div>
      )}

      {(onEdit || onDelete) && (
        <div className="mt-3 flex items-center justify-between border-t border-border-soft pt-3">
          {onEdit && (
            <button
              type="button"
              onClick={() => onEdit(bot.id)}
              className="text-xs font-medium text-text-tertiary transition-colors hover:text-text-primary"
            >
              Edit
            </button>
          )}

          {onDelete && (
            confirmingDelete ? (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-text-tertiary">Delete?</span>
                <button
                  type="button"
                  onClick={() => {
                    onDelete(bot.id);
                    setConfirmingDelete(false);
                  }}
                  className="font-medium text-red transition-colors hover:text-red/80"
                >
                  Yes
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmingDelete(false)}
                  className="font-medium text-text-tertiary transition-colors hover:text-text-primary"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setConfirmingDelete(true)}
                className="text-xs font-medium text-text-tertiary transition-colors hover:text-red"
              >
                Delete
              </button>
            )
          )}
        </div>
      )}
    </div>
  );
}
