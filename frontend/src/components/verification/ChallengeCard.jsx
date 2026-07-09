import { ArrowLeft, ArrowRight, ArrowUp, Eye, ScanFace, UserX } from "lucide-react";
import Card from "../common/Card.jsx";
import { ProgressBar } from "../common/ProgressBar.jsx";

// The backend sends a human-readable instruction string (challenge.message()),
// not a challenge code, so the icon is picked by matching keywords in it.
function iconFor(instruction = "") {
  const text = instruction.toLowerCase();
  if (text.includes("left")) return ArrowLeft;
  if (text.includes("right")) return ArrowRight;
  if (text.includes("up") || text.includes("straight")) return ArrowUp;
  if (text.includes("blink")) return Eye;
  return ScanFace;
}

export default function ChallengeCard({
  instruction,
  challengeIndex,
  challengeTotal,
  progress,
  faceDetected,
}) {
  const Icon = faceDetected === false ? UserX : iconFor(instruction);

  return (
    <Card title="Liveness Challenge" subtitle="Randomized on every attempt to prevent spoofing">
      <div className="flex flex-col items-center gap-3 py-2">
        <div
          className={`flex size-16 items-center justify-center rounded-full ${
            faceDetected === false ? "bg-[var(--color-warning)]/10" : "bg-[var(--color-brand-blue)]/10"
          }`}
        >
          <Icon
            className={`size-8 ${
              faceDetected === false ? "text-[var(--color-warning)]" : "text-[var(--color-brand-blue)]"
            }`}
          />
        </div>

        {faceDetected === false ? (
          <p className="text-center text-sm font-semibold text-[var(--color-warning)]">
            No face detected — center your face in the frame
          </p>
        ) : (
          <p className="text-center text-sm font-semibold text-[var(--color-ink)]">{instruction}</p>
        )}

        {challengeTotal ? (
          <p className="text-xs text-[var(--color-ink-faint)]">
            Challenge {Math.min(challengeIndex, challengeTotal)} of {challengeTotal}
          </p>
        ) : null}
      </div>

      <div className="mt-2 border-t border-[var(--color-border)] pt-4">
        <div className="mb-1.5 flex items-center justify-between text-xs text-[var(--color-ink-faint)]">
          <span>Capture quality</span>
          <span>{progress}%</span>
        </div>
        <ProgressBar value={progress} />
        <p className="mt-2 text-[11px] text-[var(--color-ink-faint)]">
          Once every challenge is completed, hold still and look straight at the camera to finish.
        </p>
      </div>
    </Card>
  );
}
