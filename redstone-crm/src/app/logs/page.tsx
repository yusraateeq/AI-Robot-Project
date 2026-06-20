import Sidebar from "@/src/components/Sidebar";
import Navbar from "@/src/components/Navbar";
import LogTable from "@/src/components/LogTable";
import { CallLog } from "@/src/lib/types";

// Placeholder data — swap for a fetch to /api/call-logs once available.
const CALL_LOGS: CallLog[] = [
  {
    id: "1",
    customerName: "James Carter",
    botName: "Mary-01",
    duration: "1:42",
    outcome: "transferred",
    recordingUrl: "#",
    timestamp: "2026-06-16T14:32:00Z",
  },
  {
    id: "2",
    customerName: "Linda Ahmed",
    botName: "Mary-02",
    duration: "0:58",
    outcome: "hung-up",
    recordingUrl: "#",
    timestamp: "2026-06-16T13:50:00Z",
  },
  {
    id: "3",
    customerName: "Robert Lee",
    botName: "Mary-01",
    duration: "0:21",
    outcome: "no-answer",
    recordingUrl: null,
    timestamp: "2026-06-16T13:12:00Z",
  },
  {
    id: "4",
    customerName: "Maria Gonzalez",
    botName: "Mary-03",
    duration: "2:05",
    outcome: "voicemail",
    recordingUrl: "#",
    timestamp: "2026-06-16T11:47:00Z",
  },
];

export default function LogsPage() {
  return (
    <div className="flex min-h-screen bg-base">
      <Sidebar />
      <div className="flex-1">
        <Navbar title="Call Logs" />
        <main className="p-5">
          <LogTable logs={CALL_LOGS} />
        </main>
      </div>
    </div>
  );
}