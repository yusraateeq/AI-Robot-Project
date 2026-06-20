interface StatCardProps {
  label: string;
  value: string;
  delta?: { value: string; direction: "up" | "down" };
}

export default function StatCard({ label, value, delta }: StatCardProps) {
  return (
    <div className="rounded-lg border border-border-soft bg-panel p-4 transition-colors hover:border-border-strong">
      <p className="text-xs text-text-secondary">{label}</p>
      <p className="mt-2 font-mono text-2xl font-medium text-text-primary">{value}</p>
      {delta && (
        <p
          className={
            delta.direction === "up"
              ? "mt-1 text-xs font-medium text-signal"
              : "mt-1 text-xs font-medium text-red"
          }
        >
          {delta.direction === "up" ? "↑" : "↓"} {delta.value} vs yesterday
        </p>
      )}
    </div>
  );
}