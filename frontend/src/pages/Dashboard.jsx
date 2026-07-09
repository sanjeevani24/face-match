import { Link } from "react-router-dom";
import { ScanFace } from "lucide-react";
import Statistics from "../components/dashboard/Statistics.jsx";
import RecentVerification from "../components/dashboard/RecentVerification.jsx";
import Button from "../components/common/Button.jsx";

export default function Dashboard() {
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
      <RecentVerification />
    </div>
  );
}
