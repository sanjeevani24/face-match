import { FileSearch } from "lucide-react";
import Card from "../common/Card.jsx";

const STATUS_STYLES = {
  passed: "bg-[var(--color-brand-green)]/10 text-[var(--color-brand-green)]",
  review: "bg-[var(--color-warning)]/10 text-[var(--color-warning)]",
  failed: "bg-[var(--color-danger)]/10 text-[var(--color-danger)]",
};

export default function RecentVerification({ items = [], title = "Recent Verifications", subtitle = "Latest eKYC attempts across all branches" }) {
  return (
    <Card title={title} subtitle={subtitle}>
      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
          <FileSearch className="size-8 text-[var(--color-ink-faint)]" />
          <p className="text-sm font-medium text-[var(--color-ink-soft)]">No verifications yet</p>
          <p className="max-w-xs text-xs text-[var(--color-ink-faint)]">
            Once a verification is completed, it will show up here automatically.
          </p>
        </div>
      ) : (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs text-[var(--color-ink-faint)]">
              <th className="pb-2 font-medium">Source</th>
              <th className="pb-2 font-medium">Date</th>
              <th className="pb-2 font-medium">Similarity</th>
              <th className="pb-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t border-[var(--color-border)]">
                <td className="py-2.5">{item.name}</td>
                <td className="py-2.5 text-[var(--color-ink-soft)]">{item.date}</td>
                <td className="py-2.5">{item.similarity}</td>
                <td className="py-2.5">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      STATUS_STYLES[item.status] ?? STATUS_STYLES.failed
                    }`}
                  >
                    {item.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}