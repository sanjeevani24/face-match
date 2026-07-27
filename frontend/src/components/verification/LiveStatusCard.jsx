import { ShieldCheck, ShieldAlert, ShieldQuestion, ScanFace, UserX, Radio } from "lucide-react";
import Card from "../common/Card.jsx";

function Metric({ label, value, tone = "neutral" }) {
  const toneClass = {
    good: "text-[var(--color-brand-green)]",
    warn: "text-[var(--color-warning)]",
    bad: "text-[var(--color-danger)]",
    neutral: "text-[var(--color-ink)]",
  }[tone];

  return (
    <div className="rounded-xl border border-[var(--color-border)] p-3">
      <p className="text-[11px] text-[var(--color-ink-faint)]">{label}</p>
      <p className={`text-lg font-bold ${toneClass}`}>{value}</p>
    </div>
  );
}

// `hasData` distinguishes "no status polled yet" from "checked and came
// back clean" -- without it, flagged={Boolean(undefined)} === false and
// every row silently renders as a passing "OK"/"Yes" before the bot has
// even joined, which is actively misleading rather than just empty.
function StatusRow({
  icon: OkIcon,
  badIcon: BadIcon,
  unknownIcon: UnknownIcon = ShieldQuestion,
  label,
  hasData,
  flagged,
  okLabel = "OK",
  flaggedLabel = "Flagged",
}) {
  if (!hasData) {
    return (
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-2 text-[var(--color-ink-faint)]">
          <UnknownIcon className="size-4 text-[var(--color-ink-faint)]" />
          {label}
        </span>
        <span className="font-semibold text-[var(--color-ink-faint)]">—</span>
      </div>
    );
  }

  const Icon = flagged ? BadIcon : OkIcon;
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="flex items-center gap-2 text-[var(--color-ink-faint)]">
        <Icon className={`size-4 ${flagged ? "text-[var(--color-danger)]" : "text-[var(--color-brand-green)]"}`} />
        {label}
      </span>
      <span className={`font-semibold ${flagged ? "text-[var(--color-danger)]" : "text-[var(--color-ink)]"}`}>
        {flagged ? flaggedLabel : okLabel}
      </span>
    </div>
  );
}

export default function LiveStatusCard({ status, framesAlive }) {
  const hasData = Boolean(status);

  const similarityTone =
    !hasData || status.similarity == null
      ? "neutral"
      : status.identity_flagged
      ? "bad"
      : status.similarity >= 0.55
      ? "good"
      : "warn";

  return (
    <Card title="Live Verification Status" subtitle="Updates automatically while the call is being monitored">
      <div className="flex items-center gap-2 pb-4">
        <Radio
          className={`size-4 ${
            framesAlive ? "animate-pulse text-[var(--color-brand-blue)]" : "text-[var(--color-ink-faint)]"
          }`}
        />
        <span className="text-xs text-[var(--color-ink-faint)]">
          {framesAlive ? "Frames arriving from the call" : "Waiting for frames…"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Metric
          label="Similarity"
          value={hasData && status.similarity != null ? status.similarity.toFixed(3) : "—"}
          tone={similarityTone}
        />
        <Metric label="Confidence" value={(hasData && status.confidence) || "—"} tone={similarityTone} />
      </div>

      <div className="mt-4 flex flex-col gap-2 border-t border-[var(--color-border)] pt-4">
        <StatusRow
          icon={ScanFace}
          badIcon={UserX}
          label="Face detected"
          hasData={hasData}
          flagged={status?.face_detected === false}
          okLabel="Yes"
          flaggedLabel="No"
        />
        <StatusRow
          icon={ShieldCheck}
          badIcon={ShieldAlert}
          label="Identity match"
          hasData={hasData}
          flagged={Boolean(status?.identity_flagged)}
        />
        <StatusRow
          icon={ShieldCheck}
          badIcon={ShieldAlert}
          label="Liveness / antispoof"
          hasData={hasData}
          flagged={Boolean(status?.spoof_flagged)}
        />
      </div>
    </Card>
  );
}