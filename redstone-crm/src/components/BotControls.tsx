"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { onAuthStateChanged, signOut, User } from "firebase/auth";
import { auth } from "@/src/lib/firebase";
import { cn } from "@/src/lib/cn";

const BASE_URL = "http://localhost:3002";

export default function BotControls() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [botStatus, setBotStatus] = useState<"online" | "offline" | "loading">(
    "loading"
  );
  const autoActivatedRef = useRef(false);

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, setUser);
    return unsub;
  }, []);

  useEffect(() => {
    fetch(`${BASE_URL}/api/status`)
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((data) =>
        setBotStatus(data.automation_agent ? "online" : "offline")
      )
      .catch(() => setBotStatus("offline"));
  }, []);

  useEffect(() => {
    if (autoActivatedRef.current) return;
    if (!user || botStatus !== "offline") return;
    autoActivatedRef.current = true;
    user
      .getIdToken()
      .then((idToken) =>
        fetch(`${BASE_URL}/api/activate-bot`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${idToken}`,
          },
        })
      )
      .then((res) => {
        if (res.ok) setBotStatus("online");
      })
      .catch((err) => console.error("Bot activation failed:", err));
  }, [user, botStatus]);

  const handleLogout = async () => {
    try {
      if (user) {
        const idToken = await user.getIdToken();
        await fetch(`${BASE_URL}/api/stop-bot`, {
          method: "POST",
          headers: { Authorization: `Bearer ${idToken}` },
        });
      }
    } catch {
      /* best-effort */
    }
    await signOut(auth);
    setBotStatus("offline");
    router.push("/login");
  };

  const handleRestart = async () => {
    setBotStatus("offline");
    if (user) {
      try {
        const idToken = await user.getIdToken();
        const res = await fetch(`${BASE_URL}/api/restart-bot`, {
          method: "POST",
          headers: { Authorization: `Bearer ${idToken}` },
        });
        if (res.ok) {
          setBotStatus("online");
        }
      } catch {
        setBotStatus("offline");
      }
    }
  };

  const isOnline = botStatus === "online";
  const isLoading = botStatus === "loading";

  return (
    <div className="rounded-lg border border-border-soft bg-panel p-5">
      <div className="mb-4 flex items-center gap-3">
        <span
          className={cn(
            "h-2 w-2 rounded-full",
            isOnline ? "bg-signal signal-dot" : "bg-text-tertiary"
          )}
        />
        <span
          className={cn(
            "text-sm font-medium",
            isOnline ? "text-signal" : "text-text-tertiary"
          )}
        >
          Bot Status:{" "}
          {isLoading ? "Loading\u2026" : isOnline ? "Online" : "Offline"}
        </span>
      </div>

      <div className="flex gap-2">
        {user ? (
          <button
            type="button"
            disabled
            className="flex-1 cursor-not-allowed rounded-md bg-signal/15 px-3 py-2 text-xs font-medium text-signal"
          >
            Active
          </button>
        ) : (
          <button
            type="button"
            onClick={() => router.push("/login")}
            className="flex-1 rounded-md bg-signal/15 px-3 py-2 text-xs font-medium text-signal transition-colors hover:bg-signal/25"
          >
            Login
          </button>
        )}
        <button
          type="button"
          onClick={handleLogout}
          disabled={!user || isLoading}
          className="flex-1 rounded-md border border-border-soft px-3 py-2 text-xs font-medium text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary disabled:cursor-not-allowed disabled:text-text-tertiary"
        >
          Logout
        </button>
        <button
          type="button"
          onClick={handleRestart}
          disabled={!user || isLoading}
          className="flex-1 rounded-md border border-border-soft px-3 py-2 text-xs font-medium text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary disabled:cursor-not-allowed disabled:text-text-tertiary"
        >
          Restart
        </button>
      </div>
    </div>
  );
}
