import { useEffect, useState } from "react";
import { AlertTriangle, ChevronDown, ChevronRight } from "lucide-react";
import Card from "../components/common/Card.jsx";
import { getLogs } from "../services/verificationApi.js";

function parseTimings(json) {
  if (!json) return null;
  try {
    return JSON.parse(json);
  } catch {
    return null;
  }
}

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getLogs(200)
      .then((data) => {
        if (!cancelled) setLogs(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Couldn't load logs.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-ink)]">Logs</h2>
        <p className="text-sm text-[var(--color-ink-faint)]">
          Detailed record of every verification attempt, including failures, errors, and antispoofing telemetry.
        </p>
      </div>

      {error && <p className="text-sm text-[var(--color-danger)]">{error}</p>}

      <Card>
        {logs.length === 0 ? (
          <p className="py-10 text-center text-sm text-[var(--color-ink-faint)]">No logs yet.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-xs text-[var(--color-ink-faint)]">
                <th className="pb-2 font-medium"></th>
                <th className="pb-2 font-medium">Time</th>
                <th className="pb-2 font-medium">Source</th>
                <th className="pb-2 font-medium">Decision</th>
                <th className="pb-2 font-medium">Similarity</th>
                <th className="pb-2 font-medium">Duration</th>
                <th className="pb-2 font-medium">Detail</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => {
                const isExpanded = expandedId === log.id;
                const timings = parseTimings(log.challenge_timings);

                return (
                  <>
                    <tr
                      key={log.id}
                      className="cursor-pointer border-t border-[var(--color-border)] align-top hover:bg-black/[0.02]"
                      onClick={() => setExpandedId(isExpanded ? null : log.id)}
                    >
                      <td className="py-2.5 pl-1 text-[var(--color-ink-faint)]">
                        {isExpanded ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
                      </td>
                      <td className="py-2.5 whitespace-nowrap text-[var(--color-ink-soft)]">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="py-2.5">{log.source}</td>
                      <td className="py-2.5">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                            log.level === "error"
                              ? "bg-[var(--color-danger)]/10 text-[var(--color-danger)]"
                              : log.decision === "pass"
                              ? "bg-[var(--color-brand-green)]/10 text-[var(--color-brand-green)]"
                              : log.decision === "review"
                              ? "bg-[var(--color-warning)]/10 text-[var(--color-warning)]"
                              : "bg-[var(--color-danger)]/10 text-[var(--color-danger)]"
                          }`}
                        >
                          {log.level === "error" && <AlertTriangle className="size-3" />}
                          {log.decision}
                        </span>
                      </td>
                      <td className="py-2.5">
                        {log.similarity != null ? `${(log.similarity * 100).toFixed(1)}%` : "—"}
                      </td>
                      <td className="py-2.5">
                        {log.duration_seconds != null ? `${log.duration_seconds.toFixed(2)}s` : "—"}
                      </td>
                      <td className="py-2.5 max-w-xs truncate text-[var(--color-ink-faint)]" title={log.error_message || ""}>
                        {log.error_message || "—"}
                      </td>
                    </tr>

                    {isExpanded && (
                      <tr className="border-t border-[var(--color-border)] bg-black/[0.015]">
                        <td colSpan={7} className="px-4 py-3">
                          <div className="grid grid-cols-2 gap-4 text-xs sm:grid-cols-4">
                            <div>
                              <p className="text-[var(--color-ink-faint)]">Spoof checks</p>
                              <p className="font-medium text-[var(--color-ink)]">
                                {log.spoof_checks_count ?? "—"}
                              </p>
                            </div>
                            <div>
                              <p className="text-[var(--color-ink-faint)]">Live ratio</p>
                              <p className="font-medium text-[var(--color-ink)]">
                                {log.spoof_live_ratio != null ? `${(log.spoof_live_ratio * 100).toFixed(1)}%` : "—"}
                              </p>
                            </div>
                            <div>
                              <p className="text-[var(--color-ink-faint)]">Confidence range</p>
                              <p className="font-medium text-[var(--color-ink)]">
                                {log.spoof_min_confidence != null && log.spoof_max_confidence != null
                                  ? `${log.spoof_min_confidence.toFixed(2)} – ${log.spoof_max_confidence.toFixed(2)}`
                                  : "—"}
                              </p>
                            </div>
                            <div>
                              <p className="text-[var(--color-ink-faint)]">Threshold</p>
                              <p className="font-medium text-[var(--color-ink)]">
                                {log.threshold != null ? `${(log.threshold * 100).toFixed(0)}%` : "—"}
                              </p>
                            </div>
                          </div>

                          {timings && (
                            <div className="mt-3">
                              <p className="mb-1 text-[var(--color-ink-faint)]">Challenge timings</p>
                              <div className="flex flex-wrap gap-2">
                                {Object.entries(timings).map(([name, seconds]) => (
                                  <span
                                    key={name}
                                    className="rounded-full border border-[var(--color-border)] px-2 py-0.5 text-xs"
                                  >
                                    {name}: {seconds}s
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}