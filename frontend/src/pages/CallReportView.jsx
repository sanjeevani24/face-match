import { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { FileDown, AlertTriangle, RefreshCw } from "lucide-react";
import Card from "../components/common/Card.jsx";
import Button from "../components/common/Button.jsx";
import { getCallReport, downloadReportPdf, retryAnalysis } from "../services/verificationApi.js";


export default function CallReportView() {
  const { roomId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [retrying, setRetrying] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await getCallReport(roomId);
      setReport(data);
      setPending(false);
      setError(null);
    } catch (e) {
      if (e?.response?.status === 404) {
        setPending(true); // analysis still running in background
      } else {
        setError(e?.response?.data?.detail || e.message);
      }
    } finally {
      setLoading(false);
    }
  }, [roomId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!pending) return undefined;
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, [pending, load]);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const blob = await downloadReportPdf(roomId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `kyc_report_${roomId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    } finally {
      setDownloading(false);
    }
  };

  const handleRetryAnalysis = async () => {
    setRetrying(true);
    try {
      await retryAnalysis(roomId);
      setPending(true); // triggers the polling loop above until it succeeds
    } finally {
      setRetrying(false);
    }
  };

if (loading) {
  return (
    <div className="p-6">
      <Card title="Verification Report">
        <div className="flex items-center gap-2 p-4 text-sm text-[var(--color-ink-faint)]">
          <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          Loading report…
        </div>
      </Card>
    </div>
  );
}

if (pending) {
  return (
    <div className="p-6">
      <Card title="Verification Report" subtitle={roomId}>
        <div className="flex items-center gap-2 p-4 text-sm text-[var(--color-ink-faint)]">
          <span className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          Preparing your report — transcribing the call and analyzing sentiment. This usually takes 30–90 seconds.
        </div>
      </Card>
    </div>
  );
}

  if (error) {
    return (
      <div className="p-6">
        <Card title="Verification Report">
          <p className="text-sm text-[var(--color-danger)]">{error}</p>
        </Card>
      </div>
    );
  }

  const sentiment = report.sentiment
    ? (typeof report.sentiment === "string" ? JSON.parse(report.sentiment) : report.sentiment)
    : null;

  return (
    <div className="grid grid-cols-1 gap-6 p-6">
      <Card
        title="Verification Call Report"
        subtitle={roomId}
        action={
          <Button icon={FileDown} onClick={handleDownload} loading={downloading}>
            Download PDF
          </Button>
        }
      >
        {sentiment ? (
          <>
            <div className="grid grid-cols-2 gap-4 p-4 text-sm">
              <div>
                <span className="text-[var(--color-ink-faint)]">Overall Sentiment:</span>{" "}
                {sentiment.overall_sentiment}
              </div>
              <div>
                <span className="text-[var(--color-ink-faint)]">Sentiment Score:</span>{" "}
                {sentiment.sentiment_score.toFixed(2)}
              </div>
              <div>
                <span className="text-[var(--color-ink-faint)]">Engagement:</span>{" "}
                {sentiment.engagement_level}
              </div>
              <div>
                <span className="text-[var(--color-ink-faint)]">Confidence:</span>{" "}
                {sentiment.confidence.toFixed(2)}
              </div>
            </div>

            {sentiment.deception_risk_flag && (
              <div className="mx-4 mb-4 flex items-center gap-2 rounded-lg border border-[var(--color-danger)] bg-[var(--color-danger)]/10 px-3 py-2 text-sm text-[var(--color-danger)]">
                <AlertTriangle className="size-4" />
                Deception risk flagged
              </div>
            )}

            <div className="px-4 pb-4">
              <h3 className="mb-1 text-sm font-medium">Facial Expression Summary</h3>
              <p className="text-sm text-[var(--color-ink-faint)]">{sentiment.facial_expression_summary}</p>
            </div>

            <div className="px-4 pb-4">
              <h3 className="mb-1 text-sm font-medium">Inferred Intention</h3>
              <p className="text-sm text-[var(--color-ink-faint)]">{sentiment.inferred_intention}</p>
            </div>

            {sentiment.stress_indicators?.length > 0 && (
              <div className="px-4 pb-4">
                <h3 className="mb-1 text-sm font-medium">Stress Indicators</h3>
                <ul className="list-inside list-disc text-sm text-[var(--color-ink-faint)]">
                  {sentiment.stress_indicators.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {sentiment.key_moments?.length > 0 && (
              <div className="px-4 pb-4">
                <h3 className="mb-1 text-sm font-medium">Key Moments</h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-[var(--color-ink-faint)]">
                      <th className="pb-1 pr-4">Time</th>
                      <th className="pb-1">Observation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sentiment.key_moments.map((m, i) => (
                      <tr key={i} className="border-b last:border-0">
                        <td className="py-1 pr-4 text-[var(--color-ink-faint)]">{m.approx_timestamp}</td>
                        <td className="py-1">{m.observation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        ) : (
          <div className="p-4">
            <div className="flex items-center gap-2 rounded-lg border border-[var(--color-warning,#e5a000)] bg-[var(--color-warning,#e5a000)]/10 px-3 py-2 text-sm">
              <AlertTriangle className="size-4" />
              Sentiment analysis is temporarily unavailable (service error). The call transcript below is still available.
            </div>
            <Button
              icon={RefreshCw}
              variant="outline"
              onClick={handleRetryAnalysis}
              loading={retrying}
              className="mt-3"
            >
              Retry sentiment analysis
            </Button>
          </div>
        )}
      </Card>

      <Card title="Call Transcript">
        <div className="max-h-96 overflow-y-auto p-4 text-sm whitespace-pre-wrap text-[var(--color-ink-faint)]">
          {report.transcript || "Transcript not available."}
        </div>
      </Card>
    </div>
  );
}