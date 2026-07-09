import { Menu, Bell } from "lucide-react";

export default function Header({ onMenuClick, title = "Dashboard" }) {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-[var(--color-border)] bg-white/90 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="rounded-lg p-2 text-[var(--color-ink-soft)] hover:bg-black/5 lg:hidden"
          aria-label="Open navigation"
        >
          <Menu className="size-5" />
        </button>
        <h1 className="text-base font-semibold text-[var(--color-ink)]">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        <button
          className="rounded-lg p-2 text-[var(--color-ink-soft)] hover:bg-black/5"
          aria-label="Notifications"
        >
          <Bell className="size-5" />
        </button>
        <div className="flex items-center gap-2.5 rounded-xl border border-[var(--color-border)] py-1.5 pl-1.5 pr-3">
          <div className="flex size-7 items-center justify-center rounded-full bg-[var(--color-brand-green)] text-xs font-bold text-white">
            OP
          </div>
          <div className="hidden text-left leading-tight sm:block">
            <p className="text-xs font-semibold text-[var(--color-ink)]">Verification Officer</p>
            <p className="text-[10px] text-[var(--color-ink-faint)]">Branch: Mumbai</p>
          </div>
        </div>
      </div>
    </header>
  );
}
