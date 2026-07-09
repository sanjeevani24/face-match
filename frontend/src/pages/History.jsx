import RecentVerification from "../components/dashboard/RecentVerification.jsx";

export default function History() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-ink)]">Verification History</h2>
        <p className="text-sm text-[var(--color-ink-faint)]">
          Full audit trail of past eKYC attempts. Connect a `GET /verification/history` (or similar) endpoint
          to populate this list.
        </p>
      </div>
      <RecentVerification />
    </div>
  );
}
