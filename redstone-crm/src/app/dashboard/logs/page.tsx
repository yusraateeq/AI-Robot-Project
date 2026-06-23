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
      <div className="flex min-w-0 flex-1 flex-col">
        <Navbar title="Call Logs" />
        <main className="overflow-auto p-4 md:p-5">
          <div className="overflow-x-auto rounded-lg border border-border-soft bg-panel">
            <table className="w-full min-w-[500px] text-left text-sm text-text-primary">
              <thead className="bg-panel-raised text-text-secondary">
                <tr>
                  <th className="p-3 md:p-4">Bot</th>
                  <th className="p-3 md:p-4">Customer</th>
                  <th className="p-3 md:p-4">Status</th>
                  <th className="p-3 md:p-4">Recording</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-soft">
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td className="p-3 font-mono md:p-4">{log.bot}</td>
                    <td className="p-3 md:p-4">{log.customer}</td>
                    <td className="p-3 text-signal md:p-4">{log.status}</td>
                    <td className="w-48 p-3 md:w-64 md:p-4">
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