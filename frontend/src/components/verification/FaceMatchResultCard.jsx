import { CheckCircle2, XCircle, AlertCircle, ShieldOff, RotateCcw } from "lucide-react";
import Card from "../common/Card.jsx";
import Button from "../common/Button.jsx";

const STATUS_CONFIG = {
  MATCH: {
    icon: CheckCircle2,
    iconClass: "text-[var(--color-brand-green)]",
    bgClass: "bg-[var(--color-brand-green)]/10",
    title: "Face Match Confirmed",
    message: "The selfie matches the Aadhaar photo and passed antispoofing checks.",
  },
  REVIEW: {
    icon: AlertCircle,
    iconClass: "text-[var(--color-warning)]",
    bgClass: "bg-[var(--color-warning)]/10",
    title: "Pending Review",
    message: "Similarity is in the borderline range. Flagged for manual review.",
  },
  NO_MATCH: {
    icon: XCircle,
    iconClass: "text-[var(--color-danger)]",
    bgClass: "bg-[var(--color-danger)]/10",
    title: "No Match",
    message: "The selfie does not match the Aadhaar photo closely enough.",
  },
  REJECTED: {
    icon: ShieldOff,
    iconClass: "text-[var(--color-danger)]",
    bgClass: "bg-[var(--color-danger)]/10",
    title: "Spoof Detected",
    message: "The selfie failed antispoofing — it doesn't appear to be a live photo of a real person.",
  },
};

export default function FaceMatchResultCard({ result, aadhaarPreview, selfiePreview, onRestart }) {
  if (!result) return null;

  const status = STATUS_CONFIG[result.status] ?? STATUS_CONFIG.NO_MATCH;
  const Icon = status.icon;

  // REJECTED responses never include similarity_score — spoof check
  // short-circuits before comparison ever runs.
  const hasSimilarity = typeof result.similarity_score === "number";

  return (
    <Card>
      <div className="flex flex-col items-center gap-3 py-2 text-center">
        <div className={`flex size-16 items-center justify-center rounded-full ${status.bgClass}`}>
          <Icon className={`size-9 ${status.iconClass}`} />
        </div>
        <h3 className="text-lg font-bold text-[var(--color-ink)]">{status.title}</h3>
        <p className="max-w-sm text-sm text-[var(--color-ink-faint)]">{status.message}</p>

        {hasSimilarity && (
          <div className="mt-2 grid w-full max-w-xs grid-cols-1 gap-3">
            <div className="rounded-xl border border-[var(--color-border)] p-3">
              <p className="text-[11px] text-[var(--color-ink-faint)]">Similarity Score</p>
              <p className="text-lg font-bold text-[var(--color-ink)]">
                {(result.similarity_score * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        )}

        {result.liveness && (
        <p className="text-xs text-[var(--color-ink-faint)]">
            Liveness: <span className="font-semibold">{result.liveness.is_live ? "Live" : "Not Live"}</span>
            {typeof result.liveness.confidence === "number" && ` (confidence: ${result.liveness.confidence.toFixed(3)})`}
        </p>
        )}

        <div className="mt-2 flex gap-3">
          {aadhaarPreview && (
            <img src={aadhaarPreview} alt="Aadhaar" className="h-24 w-24 rounded-xl border border-[var(--color-border)] object-cover" />
          )}
          {selfiePreview && (
            <img src={selfiePreview} alt="Selfie" className="h-24 w-24 rounded-xl border border-[var(--color-border)] object-cover" />
          )}
        </div>

        <div className="mt-4">
          <Button variant="outline" icon={RotateCcw} onClick={onRestart}>
            Run Another Check
          </Button>
        </div>
      </div>
    </Card>
  );
}