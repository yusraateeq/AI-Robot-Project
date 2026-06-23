"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Sidebar from "@/src/components/Sidebar";
import Navbar from "@/src/components/Navbar";
import BotCard from "@/src/components/BotCard";
import BotFormModal from "@/src/components/BotFormModal";
import { Bot } from "@/src/lib/types";
import { addBot, deleteBot, fetchBotStatuses, loginBot, loginBotPoll, logoutBot, restartBot, type BotStatusInfo } from "@/src/lib/api";
import type { BotStatus } from "@/src/lib/types";

export default function BotsPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const mountedRef = useRef(false);
  const [editingBot, setEditingBot] = useState<Bot | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [loading, setLoading] = useState(true);

  const activeCount = bots.filter((b) => b.status === "active").length;
  const modalOpen = isAdding || editingBot !== null;

  const fetchBotsData = useCallback(async (): Promise<Bot[]> => {
    const data = await fetchBotStatuses();
    return data.map((b: BotStatusInfo) => {
      let status: BotStatus = "offline";
      if (b.status === "restarting") status = "restarting";
      else if (b.status === "active" || b.active) status = "active";
      return { id: b.id, name: b.name, campaign: b.campaign, status, callsToday: b.callsToday ?? 0 };
    });
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    let cancelled = false;
    fetchBotsData().then((result) => {
      if (cancelled) return;
      setBots(result);
    }).catch(() => {}).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [fetchBotsData]);

  useEffect(() => {
    const interval = setInterval(() => {
      fetchBotsData().then(setBots).catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [fetchBotsData]);

  async function handleSave(data: { name: string; campaign: string }) {
    if (editingBot) {
      setBots((prev) =>
        prev.map((b) =>
          b.id === editingBot.id ? { ...b, name: data.name, campaign: data.campaign } : b
        )
      );
    } else {
      try {
        const result = await addBot(data.name, data.campaign);
        setBots((prev) => [...prev, result.bot]);
      } catch (e: unknown) {
        alert(e instanceof Error ? e.message : "Failed to add bot");
        return;
      }
    }
    closeModal();
  }

  async function handleDelete(botId: string) {
    try {
      await deleteBot(botId);
      setBots((prev) => prev.filter((b) => b.id !== botId));
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Failed to delete bot");
    }
  }

  function closeModal() {
    setIsAdding(false);
    setEditingBot(null);
  }

  if (!mountedRef.current || loading) {
    return (
      <div className="flex min-h-screen bg-base">
        <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Navbar title="AI bots" />
        <main className="overflow-auto p-4 md:p-5">
          <p className="text-sm text-text-tertiary">Loading…</p>
        </main>
      </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-base">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Navbar title="AI bots" />
        <main className="overflow-auto p-4 md:p-5">
          <div className="mb-4 flex items-center justify-between md:mb-5">
            <p className="text-sm text-text-secondary">
              {activeCount} of {bots.length} bots active
            </p>
            <button
              type="button"
              onClick={() => setIsAdding(true)}
              className="rounded-md bg-signal px-4 py-2 text-xs font-medium text-base transition-opacity hover:opacity-90"
            >
              + Add bot
            </button>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {bots.map((bot) => (
              <BotCard
                key={bot.id}
                bot={bot}
                onLogin={async (id) => {
                  try {
                    await loginBot(id);
                    await loginBotPoll(id);
                    setBots(await fetchBotsData());
                  } catch (e: unknown) {
                    const msg = e instanceof Error ? e.message : "Login failed";
                    alert(`Login failed for ${id}: ${msg}`);
                  }
                }}
                onLogout={async (id) => {
                  await logoutBot(id);
                  setBots(await fetchBotsData());
                }}
                onRestart={async (id) => {
                  setBots((prev) =>
                    prev.map((b) =>
                      b.id === id ? { ...b, status: "restarting" } : b
                    )
                  );
                  const result = await restartBot(id);
                  setBots((prev) =>
                    prev.map((b) =>
                      b.id === id
                        ? { ...b, status: result.status === "ok" ? "active" : "offline" }
                        : b
                    )
                  );
                }}
                onEdit={() => setEditingBot(bot)}
                onDelete={handleDelete}
              />
            ))}
          </div>

          {bots.length === 0 && (
            <div className="rounded-lg border border-dashed border-border-soft py-16 text-center">
              <p className="text-sm text-text-tertiary">No bots yet. Add one to get started.</p>
            </div>
          )}
        </main>
      </div>

      {modalOpen && (
        <BotFormModal bot={editingBot} onClose={closeModal} onSave={handleSave} />
      )}
    </div>
  );
}