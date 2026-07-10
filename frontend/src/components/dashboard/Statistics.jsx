import { useEffect, useState } from "react";
import { CheckCircle2, XCircle, Clock, Users } from "lucide-react";
import { getDashboardStats } from "../../services/verificationApi.js";

function formatDuration(seconds) {
  if (seconds == null) return "—";
  return `${seconds.toFixed(1)}s`;
}

export default function Statistics() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getDashboardStats()
      .then((data) => {
        if (!cancelled) setStats(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Couldn't load stats.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const cards = [
    {
      label: "Total Verifications",
      value: stats ? stats.total : "—",
      icon: Users,
      tint: "bg-[var(--color-brand-blue)]/10 text-[var(--color-brand-blue)]",
    },
    {
      label: "Passed",
      value: stats ? stats.passed : "—",
      icon: CheckCircle2,
      tint: "bg-[var(--color-brand-green)]/10 text-[var(--color-brand-green)]",
    },
    {
      label: "Failed",
      value: stats ? stats.failed : "—",
      icon: XCircle,
      tint: "bg-[var(--color-danger)]/10 text-[var(--color-danger)]",
    },
    {
      label: "Avg. Time",
      value: stats ? formatDuration(stats.avg_duration_seconds) : "—",
      icon: Clock,
      tint: "bg-[var(--color-warning)]/10 text-[var(--color-warning)]",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map(({ label, value, icon: Icon, tint }) => (
        <div key={label} className="card p-5">
          <div className={`mb-3 flex size-10 items-center justify-center rounded-xl ${tint}`}>
            <Icon className="size-5" />
          </div>
          <p className="text-2xl font-bold text-[var(--color-ink)]">{value}</p>
          <p className="mt-1 text-xs text-[var(--color-ink-faint)]">{label}</p>
        </div>
      ))}
      {error && (
        <p className="col-span-full text-xs text-[var(--color-danger)]">{error}</p>
      )}
    </div>
  );
}