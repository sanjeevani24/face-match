import { useEffect, useState } from "react";
import RecentVerification from "../components/dashboard/RecentVerification.jsx";
import { getHistory } from "../services/verificationApi.js";

function mapRecordToRow(record) {
  return {
    id: record.id,
    name: record.source === "liveness_session" ? "Live Verification" : "Face Match Check",
    date: new Date(record.created_at).toLocaleString(),
    similarity: record.similarity != null ? `${(record.similarity * 100).toFixed(1)}%` : "—",
    status: record.decision === "pass" ? "passed" : record.decision === "review" ? "review" : "failed",
  };
}

export default function History() {
  const [records, setRecords] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getHistory(100)
      .then((data) => {
        if (!cancelled) setRecords(data.map(mapRecordToRow));
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Couldn't load verification history.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-ink)]">Verification History</h2>
        <p className="text-sm text-[var(--color-ink-faint)]">
          Full audit trail of past eKYC attempts.
        </p>
      </div>
      {error && <p className="text-sm text-[var(--color-danger)]">{error}</p>}
      <RecentVerification items={records} title="All Verifications" subtitle="Complete history across all branches" />
    </div>
  );
}