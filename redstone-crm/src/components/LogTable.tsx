import { CallLog, CallOutcome } from "../lib/types";

interface LogTableProps {
  logs: CallLog[];
}

const OUTCOME_CONFIG: Record<CallOutcome, { label: string; text: string; ring: string }> = {
  transferred: { label: "Transferred", text: "text-signal", ring: "border-signal/30 bg-signal/10" },
  "no-answer": { label: "No answer", text: "text-text-tertiary", ring: "border-border-soft bg-panel-raised" },
  "hung-up": { label: "Hung up", text: "text-red", ring: "border-red/30 bg-red/10" },
  voicemail: { label: "Voicemail", text: "text-amber", ring: "border-amber/30 bg-amber/10" },
};

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function LogTable({ logs }: LogTableProps) {
  if (logs.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border-soft py-16 text-center">
        <p className="text-sm text-text-tertiary">No calls logged yet.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border-soft bg-panel">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-border-soft bg-panel-raised text-xs text-text-tertiary">
            <th className="px-4 py-3 font-medium">Customer</th>
            <th className="px-4 py-3 font-medium">Bot</th>
            <th className="px-4 py-3 font-medium">Duration</th>
            <th className="px-4 py-3 font-medium">Outcome</th>
            <th className="px-4 py-3 font-medium">Recording</th>
            <th className="px-4 py-3 font-medium">Date</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => {
            const outcome = OUTCOME_CONFIG[log.outcome];
            return (
              <tr
                key={log.id}
                className="border-b border-border-soft last:border-0 hover:bg-panel-raised/60"
              >
                <td className="px-4 py-3 font-medium text-text-primary">
                  {log.customerName}
                </td>
                <td className="px-4 py-3 font-mono text-text-secondary">{log.botName}</td>
                <td className="px-4 py-3 font-mono text-text-secondary">{log.duration}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${outcome.ring} ${outcome.text}`}
                  >
                    {outcome.label}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {log.recordingUrl ? (
                    <a
                      href={log.recordingUrl}
                      className="font-medium text-signal underline-offset-2 hover:underline"
                    >
                      Play
                    </a>
                  ) : (
                    <span className="text-text-tertiary">—</span>
                  )}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-text-tertiary">
                  {formatTimestamp(log.timestamp)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}