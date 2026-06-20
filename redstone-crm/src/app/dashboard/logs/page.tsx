"use client";

import Sidebar from "@/src/components/Sidebar";
import Navbar from "@/src/components/Navbar";
import { AudioPlayer } from "@/src/components/AudioPlayer"; // Wo component jo abhi banaya tha

const logs = [
  { id: 1, bot: "Mary-1", customer: "+1 555-0101", duration: "2:45", status: "Transferred" },
  { id: 2, bot: "Mary-2", customer: "+1 555-0102", duration: "0:30", status: "Hung up" },
];

export default function CallLogsPage() {
  return (
    <div className="flex min-h-screen bg-base">
      <Sidebar />
      <div className="flex-1">
        <Navbar title="Call Logs" />
        <main className="p-5">
          <div className="rounded-lg border border-border-soft bg-panel overflow-hidden">
            <table className="w-full text-left text-sm text-text-primary">
              <thead className="bg-panel-raised text-text-secondary">
                <tr>
                  <th className="p-4">Bot</th>
                  <th className="p-4">Customer</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Recording</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-soft">
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td className="p-4 font-mono">{log.bot}</td>
                    <td className="p-4">{log.customer}</td>
                    <td className="p-4 text-signal">{log.status}</td>
                    <td className="p-4 w-64">
                      {/* Yahan WaveSurfer component show hoga */}
                      <AudioPlayer url={`/recordings/${log.id}.mp3`} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </main>
      </div>
    </div>
  );
}