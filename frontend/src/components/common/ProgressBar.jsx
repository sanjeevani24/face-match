import { Check } from "lucide-react";

export function ProgressBar({ value = 0, className = "" }) {
  const clamped = Math.min(100, Math.max(0, value));
  return (
    <div className={`h-2 w-full overflow-hidden rounded-full bg-[var(--color-border)] ${className}`}>
      <div
        className="h-full rounded-full bg-[var(--color-brand-green)] transition-all duration-500 ease-out"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}

export function StepIndicator({ steps, currentIndex }) {
  return (
    <div className="flex items-center">
      {steps.map((label, i) => {
        const isDone = i < currentIndex;
        const isActive = i === currentIndex;
        return (
          <div key={label} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`flex size-7 items-center justify-center rounded-full text-xs font-semibold transition-colors ${
                  isDone
                    ? "bg-[var(--color-brand-green)] text-white"
                    : isActive
                    ? "bg-[var(--color-brand-blue)] text-white"
                    : "bg-[var(--color-border)] text-[var(--color-ink-faint)]"
                }`}
              >
                {isDone ? <Check className="size-3.5" /> : i + 1}
              </div>
              <span
                className={`text-[11px] whitespace-nowrap ${
                  isActive ? "font-semibold text-[var(--color-ink)]" : "text-[var(--color-ink-faint)]"
                }`}
              >
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div
                className={`mx-2 h-px flex-1 ${isDone ? "bg-[var(--color-brand-green)]" : "bg-[var(--color-border)]"}`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
