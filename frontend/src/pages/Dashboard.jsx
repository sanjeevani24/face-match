import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ScanFace } from "lucide-react";
import Statistics from "../components/dashboard/Statistics.jsx";
import RecentVerification from "../components/dashboard/RecentVerification.jsx";
import Button from "../components/common/Button.jsx";
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

export default function Dashboard() {
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    let cancelled = false;
    getHistory(5)
      .then((data) => {
        if (!cancelled) setRecent(data.map(mapRecordToRow));
      })
      .catch(() => {
        // Statistics already surfaces a load error; keep this silent to avoid duplicate messaging.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-bold text-[var(--color-ink)]">Welcome back</h2>
          <p className="text-sm text-[var(--color-ink-faint)]">
            Here's an overview of your branch's eKYC activity.
          </p>
        </div>
        <Link to="/verification">
          <Button icon={ScanFace}>Start New Verification</Button>
        </Link>
      </div>

      <Statistics />
      <RecentVerification items={recent} />
    </div>
  );
}