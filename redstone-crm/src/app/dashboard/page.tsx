"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from "chart.js";
import Sidebar from "@/src/components/Sidebar";
import Navbar from "@/src/components/Navbar";
import StatCard from "@/src/components/StatCard";
import { fetchStats, fetchBotStatuses, type DashboardStats, type BotStatusInfo } from "@/src/lib/api";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const EMPTY_STATS: DashboardStats = {
  total_calls: 0,
  transfers: 0,
  success_rate: 0,
  active_bots: 0,
  call_volume: { labels: ["9am", "11am", "1pm", "3pm", "5pm"], data: [0, 0, 0, 0, 0] },
};

function CallsChart({ stats }: { stats: DashboardStats }) {
  return (
    <Line
      data={{
        labels: stats.call_volume.labels,
        datasets: [{
          label: "Calls Today",
          data: stats.call_volume.data,
          borderColor: "#3DDC84",
          tension: 0.4,
          fill: false,
        }],
      }}
      options={{ responsive: true, maintainAspectRatio: false }}
    />
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>(EMPTY_STATS);
  const [bots, setBots] = useState<BotStatusInfo[]>([]);
  const [online, setOnline] = useState(true);
  const [loaded, setLoaded] = useState(false);

  const fetchDashboardData = useCallback(async () => {
    const [s, b] = await Promise.all([fetchStats(), fetchBotStatuses()]);
    return { stats: s, bots: b };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchDashboardData().then((result) => {
      if (cancelled) return;
      setStats(result.stats);
      setBots(result.bots);
      setOnline(true);
      setLoaded(true);
    }).catch(() => {
      if (!cancelled) setOnline(false);
    });
    const id = setInterval(() => {
      fetchDashboardData().then((result) => {
        setStats(result.stats);
        setBots(result.bots);
        setOnline(true);
        setLoaded(true);
      }).catch(() => setOnline(false));
    }, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, [fetchDashboardData]);

  return (
    <div className="flex min-h-screen bg-base">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Navbar title="Dashboard" />
        <main className="space-y-5 overflow-auto p-4 md:p-5">
          {!online && loaded && (
            <div className="rounded-lg border border-red/30 bg-red-dim/20 px-3 py-2.5 text-xs font-medium text-red md:px-4 md:py-3 md:text-sm">
              ⚠ System Offline — Backend se connection nahi ho pa raha
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 md:gap-4 lg:grid-cols-4">
            <StatCard label="Total calls today" value={String(stats.total_calls)} />
            <StatCard label="Transfers" value={String(stats.transfers)} />
            <StatCard label="Active bots" value={String(stats.active_bots)} />
            <StatCard label="Success rate" value={`${stats.success_rate}%`} />
          </div>

          <div className="h-40 rounded-lg border border-border-soft bg-panel p-4 md:h-48">
            <h2 className="text-xs text-text-tertiary mb-2">Live Call Volume</h2>
            <CallsChart stats={stats} />
          </div>

          <div className="flex items-center justify-between border-b border-border-soft px-4 py-4 md:px-5">
            <h2 className="text-sm font-semibold text-text-primary">Bot status</h2>
            <Link
              href="/dashboard/bots"
              className="text-xs font-medium text-text-secondary transition-colors hover:text-signal"
            >
              Manage bots →
            </Link>
          </div>
          <ul className="divide-y divide-border-soft">
            {bots.length === 0 && !loaded && (
              <li className="px-4 py-3 text-sm text-text-tertiary md:px-5">Loading…</li>
            )}
            {bots.length === 0 && loaded && (
              <li className="px-4 py-3 text-sm text-text-tertiary md:px-5">No bots found in backend</li>
            )}
            {bots.map((bot) => {
              const dotColor = bot.status === "active" ? "bg-signal signal-dot" : bot.status === "online" ? "bg-sky-400 signal-dot" : "bg-text-tertiary";
              const label = bot.status === "active" ? "Active" : bot.status === "online" ? "Online" : "Offline";
              const labelColor = bot.status === "active" ? "var(--color-signal)" : bot.status === "online" ? "#38bdf8" : "var(--color-text-tertiary)";
              const borderColor = bot.status === "active" ? "rgba(61,220,132,0.3)" : bot.status === "online" ? "rgba(56,189,248,0.3)" : "var(--color-border-soft)";
              const bgColor = bot.status === "active" ? "rgba(61,220,132,0.1)" : bot.status === "online" ? "rgba(56,189,248,0.1)" : "var(--color-panel-raised)";
              return (
              <li key={bot.id} className="flex items-center justify-between gap-2 px-4 py-3 md:px-5">
                <div className="flex items-center gap-3">
                  <span className={`h-2 w-2 rounded-full ${dotColor}`} />
                  <div>
                    <p className="font-mono text-sm font-medium text-text-primary">{bot.name}</p>
                    <p className="text-xs text-text-secondary">{bot.campaign}</p>
                  </div>
                </div>
                <span className="flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium"
                  style={{
                    borderColor,
                    backgroundColor: bgColor,
                    color: labelColor,
                  }}
                >
                  <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
                  {label}
                </span>
              </li>
              );
            })}
          </ul>
        </main>
      </div>
    </div>
  );
}
