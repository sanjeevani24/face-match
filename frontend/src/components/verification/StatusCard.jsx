import Card from "../common/Card.jsx";
import { ProgressBar, StepIndicator } from "../common/ProgressBar.jsx";

const STEP_LABELS = ["Upload", "Live Challenge", "Result"];

export default function StatusCard({ stepIndex, progress, message }) {
  return (
    <Card padded={false} className="p-5">
      <StepIndicator steps={STEP_LABELS} currentIndex={stepIndex} />
      <div className="mt-5">
        <ProgressBar value={progress} />
        {message && <p className="mt-2 text-xs text-[var(--color-ink-faint)]">{message}</p>}
      </div>
    </Card>
  );
}
