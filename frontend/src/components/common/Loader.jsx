import { Loader2 } from "lucide-react";

export default function Loader({ label = "Loading…", size = "md", className = "" }) {
  const sizes = { sm: "size-4", md: "size-6", lg: "size-10" };
  return (
    <div className={`flex flex-col items-center justify-center gap-2 text-[var(--color-ink-soft)] ${className}`}>
      <Loader2 className={`${sizes[size]} animate-spin text-[var(--color-brand-blue)]`} />
      {label && <span className="text-xs">{label}</span>}
    </div>
  );
}
