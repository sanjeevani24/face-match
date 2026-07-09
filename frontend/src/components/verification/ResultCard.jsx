import { CheckCircle2, XCircle, AlertCircle, RotateCcw, Download } from "lucide-react";
import Card from "../common/Card.jsx";
import Button from "../common/Button.jsx";
import { formatConfidence } from "../../utils/media.js";
import { MATCH_THRESHOLD } from "../../utils/constants.js";

const STATUS_CONFIG = {
  pass: {
    icon: CheckCircle2,
    iconClass: "text-[var(--color-brand-green)]",
    bgClass: "bg-[var(--color-brand-green)]/10",
    title: "Identity Verified",
    message:
      "The live capture matches the Aadhaar photo within the required confidence threshold.",
  },
  review: {
    icon: AlertCircle,
    iconClass: "text-[var(--color-warning)]",
    bgClass: "bg-[var(--color-warning)]/10",
    title: "Pending Review",
    message:
      "The similarity score is close to the threshold. This verification has been flagged for manual review rather than an automatic decision.",
  },
  fail: {
    icon: XCircle,
    iconClass: "text-[var(--color-danger)]",
    bgClass: "bg-[var(--color-danger)]/10",
    title: "Verification Failed",
    message:
      "The live capture did not match the Aadhaar photo closely enough. Please try again with better lighting and a clear, front-facing view.",
  },
};

export default function ResultCard({ result, liveFrame, onRestart }) {
  if (!result) return null;

  // Backend now returns `decision`: "pass" | "review" | "fail".
  // Fall back to the old boolean `match` field for safety in case an
  // older cached response or a different endpoint still sends that shape.
  const decision =
    result.decision ?? (result.match ? "pass" : "fail");

  const status = STATUS_CONFIG[decision] ?? STATUS_CONFIG.fail;
  const Icon = status.icon;

  const similarity = result.similarity ?? null;
  const threshold = result.threshold ?? MATCH_THRESHOLD;

  return (
    <Card>
      <div className="flex flex-col items-center gap-3 py-2 text-center">
        <div className={`flex size-16 items-center justify-center rounded-full ${status.bgClass}`}>
          <Icon className={`size-9 ${status.iconClass}`} />
        </div>
        <h3 className="text-lg font-bold text-[var(--color-ink)]">{status.title}</h3>
        <p className="max-w-sm text-sm text-[var(--color-ink-faint)]">{status.message}</p>

        <div className="mt-2 grid w-full max-w-xs grid-cols-2 gap-3">
          <div className="rounded-xl border border-[var(--color-border)] p-3">
            <p className="text-[11px] text-[var(--color-ink-faint)]">Similarity</p>
            <p className="text-lg font-bold text-[var(--color-ink)]">{formatConfidence(similarity)}</p>
          </div>
          <div className="rounded-xl border border-[var(--color-border)] p-3">
            <p className="text-[11px] text-[var(--color-ink-faint)]">Threshold</p>
            <p className="text-lg font-bold text-[var(--color-ink)]">{formatConfidence(threshold)}</p>
          </div>
        </div>

        {result.confidence && (
          <p className="text-xs text-[var(--color-ink-faint)]">
            Confidence: <span className="font-semibold">{result.confidence}</span>
          </p>
        )}

        {liveFrame && (
          <img
            src={liveFrame}
            alt="Captured live frame"
            className="mt-2 h-24 w-24 rounded-xl border border-[var(--color-border)] object-cover [transform:scaleX(-1)]"
          />
        )}

        <div className="mt-4 flex gap-3">
          <Button variant="outline" icon={RotateCcw} onClick={onRestart}>
            Start New Verification
          </Button>
          <Button variant="ghost" icon={Download} disabled title="Wire this up once a report/export endpoint exists">
            Download Report
          </Button>
        </div>
      </div>
    </Card>
  );
}