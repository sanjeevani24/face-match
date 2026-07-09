import { FileSearch } from "lucide-react";
import Card from "../common/Card.jsx";

export default function RecentVerification({ items = [] }) {
  return (
    <Card title="Recent Verifications" subtitle="Latest eKYC attempts across all branches">
      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
          <FileSearch className="size-8 text-[var(--color-ink-faint)]" />
          <p className="text-sm font-medium text-[var(--color-ink-soft)]">No verifications yet</p>
          <p className="max-w-xs text-xs text-[var(--color-ink-faint)]">
            Once a history endpoint is available on the backend, results will list here automatically.
          </p>
        </div>
      ) : (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs text-[var(--color-ink-faint)]">
              <th className="pb-2 font-medium">Name</th>
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
                      item.status === "passed"
                        ? "bg-[var(--color-brand-green)]/10 text-[var(--color-brand-green)]"
                        : "bg-[var(--color-danger)]/10 text-[var(--color-danger)]"
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
