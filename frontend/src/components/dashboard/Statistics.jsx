import { CheckCircle2, XCircle, Clock, Users } from "lucide-react";

const STATS = [
  { label: "Total Verifications", value: "—", icon: Users, tint: "bg-[var(--color-brand-blue)]/10 text-[var(--color-brand-blue)]" },
  { label: "Passed", value: "—", icon: CheckCircle2, tint: "bg-[var(--color-brand-green)]/10 text-[var(--color-brand-green)]" },
  { label: "Failed", value: "—", icon: XCircle, tint: "bg-[var(--color-danger)]/10 text-[var(--color-danger)]" },
  { label: "Avg. Time", value: "—", icon: Clock, tint: "bg-[var(--color-warning)]/10 text-[var(--color-warning)]" },
];

export default function Statistics() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {STATS.map(({ label, value, icon: Icon, tint }) => (
        <div key={label} className="card p-5">
          <div className={`mb-3 flex size-10 items-center justify-center rounded-xl ${tint}`}>
            <Icon className="size-5" />
          </div>
          <p className="text-2xl font-bold text-[var(--color-ink)]">{value}</p>
          <p className="mt-1 text-xs text-[var(--color-ink-faint)]">{label}</p>
        </div>
      ))}
      <p className="col-span-full text-xs text-[var(--color-ink-faint)]">
        Connect <code className="rounded bg-black/5 px-1 py-0.5">GET /verification/result</code> (or an
        analytics endpoint once available) to populate these figures from real data.
      </p>
    </div>
  );
}
